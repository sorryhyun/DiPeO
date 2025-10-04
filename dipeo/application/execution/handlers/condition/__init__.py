"""Refactored condition node handler using evaluator pattern."""

import json
import logging
import time
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.execution.handlers.utils import get_node_execution_count
from dipeo.application.registry.keys import EXECUTION_ORCHESTRATOR, PROMPT_BUILDER
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.condition_node import ConditionNode, NodeType
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

from .evaluators import (
    ConditionEvaluator,
    CustomExpressionEvaluator,
    MaxIterationsEvaluator,
    NodesExecutedEvaluator,
)
from .evaluators.llm_decision_evaluator import LLMDecisionEvaluator

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext

logger = get_module_logger(__name__)


@register_handler
@requires_services(
    execution_orchestrator=(EXECUTION_ORCHESTRATOR, Optional),
    prompt_builder=(PROMPT_BUILDER, Optional),
)
class ConditionNodeHandler(TypedNodeHandler[ConditionNode]):
    """Handler for condition nodes using evaluator pattern with envelope support."""

    NODE_TYPE = NodeType.CONDITION

    def __init__(self):
        super().__init__()
        self._evaluators: dict[str, ConditionEvaluator] = {
            "detect_max_iterations": MaxIterationsEvaluator(),
            "check_nodes_executed": NodesExecutedEvaluator(),
            "custom": CustomExpressionEvaluator(),
            "llm_decision": LLMDecisionEvaluator(),
        }

    @property
    def node_class(self) -> type[ConditionNode]:
        return ConditionNode

    @property
    def node_type(self) -> str:
        return NodeType.CONDITION.value

    @property
    def schema(self) -> type[BaseModel]:
        return ConditionNode

    @property
    def description(self) -> str:
        return "Evaluates conditions using specialized evaluators for different condition types"

    def validate(self, request: ExecutionRequest[ConditionNode]) -> str | None:
        if not request.context or not hasattr(request.context, "diagram"):
            return "Executable diagram not available in context"

        node = request.node
        condition_type = node.condition_type

        if condition_type not in self._evaluators:
            supported = ", ".join(self._evaluators.keys())
            return f"Unsupported condition type: {condition_type}. Supported types: {supported}"

        if condition_type == "custom" and not node.expression:
            return "Custom condition requires an expression"

        if condition_type == "check_nodes_executed" and not node.node_indices:
            return "check_nodes_executed requires node_indices"

        if condition_type == "llm_decision":
            if not hasattr(node, "person") or not node.person:
                return "llm_decision requires a person to be specified"
            if not hasattr(node, "judge_by") and not hasattr(node, "judge_by_file"):
                return "llm_decision requires either judge_by or judge_by_file"

        return None

    async def pre_execute(self, request: ExecutionRequest[ConditionNode]) -> Envelope | None:
        """Pre-execution setup: validate services and select evaluator.

        Moves evaluator selection and service validation out of execute_request
        for cleaner separation of concerns.
        """
        node = request.node
        condition_type = node.condition_type

        # Get the currently executing diagram from the context
        diagram = request.context.diagram if request.context else None
        if diagram is None:
            return EnvelopeFactory.create(
                body="Executable diagram not available in context",
                produced_by=node.id,
                trace_id=request.execution_id or "",
                error="ValueError",
            )

        # Select and validate evaluator
        evaluator = self._evaluators.get(condition_type)
        if not evaluator:
            logger.error(f"No evaluator found for condition type: {condition_type}")
            return EnvelopeFactory.create(
                body=f"No evaluator for condition type: {condition_type}",
                produced_by=node.id,
                trace_id=request.execution_id or "",
                meta={"error_type": "ValueError", "is_error": True},
            )

        # Store evaluator in request state
        request.set_handler_state("evaluator", evaluator)

        # No early return - proceed to execute_request
        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[ConditionNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare inputs with token consumption.

        Phase 5: Now consumes tokens from incoming edges when available.
        """
        from dipeo.diagram_generated.enums import ContentType

        # Phase 5: Consume tokens from incoming edges or fall back to regular inputs
        envelope_inputs = self.get_effective_inputs(request, inputs)

        # Convert envelopes to appropriate format based on content type
        legacy_inputs = {}
        for key, envelope in envelope_inputs.items():
            if envelope.content_type == ContentType.CONVERSATION_STATE:
                # Handle conversation state specifically
                legacy_inputs[key] = envelope.as_conversation()
            else:
                # Use parent's default conversion for other types
                try:
                    # Try to parse as JSON first
                    legacy_inputs[key] = envelope.as_json()
                except ValueError:
                    # Fall back to text
                    legacy_inputs[key] = envelope.as_text()

        return legacy_inputs

    async def run(
        self, inputs: dict[str, Any], request: ExecutionRequest[ConditionNode]
    ) -> dict[str, Any]:
        """Execute condition evaluation."""
        node = request.node
        context = request.context
        legacy_inputs = inputs

        # Use evaluator from request state (set in pre_execute)
        evaluator = request.get_handler_state("evaluator")

        # For LLM decision evaluator, pass required services
        if node.condition_type == "llm_decision" and hasattr(evaluator, "set_services"):
            evaluator.set_services(
                orchestrator=self._execution_orchestrator,
                prompt_builder=self._prompt_builder,
            )

        # Track and expose loop index if configured
        if hasattr(node, "expose_index_as") and node.expose_index_as:
            # Use the execution count directly as loop index (0-based)
            # The execution count is incremented BEFORE run() is called,
            # so we subtract 1 to get a 0-based index
            execution_count = get_node_execution_count(context, node.id)
            current_loop_index = max(0, execution_count - 1)  # 0-based index
            context.set_variable(node.expose_index_as, current_loop_index)

            logger.debug(
                f"ConditionNode {node.id}: Exposing loop index as '{node.expose_index_as}' = {current_loop_index} (execution_count={execution_count})"
            )

        # Execute evaluation with pre-selected evaluator
        eval_result = await evaluator.evaluate(node, context, legacy_inputs)
        result = eval_result["result"]
        output_value = eval_result["output_data"] or {}

        # Get evaluation metadata
        evaluation_metadata = eval_result["metadata"]

        # Return only the active branch data
        active_branch = "condtrue" if result else "condfalse"

        # Return structured result for serialization
        # The output_value goes directly in the response, not wrapped
        return {
            "result": result,
            "active_branch": active_branch,
            "branch_data": output_value,  # Direct pass-through of active branch data
            "condition_type": node.condition_type,
            "evaluation_metadata": evaluation_metadata,
            "timestamp": time.time(),
        }

    def serialize_output(self, result: Any, request: ExecutionRequest[ConditionNode]) -> Envelope:
        """Serialize condition result to envelope with branch data."""
        node = request.node
        context = request.context

        # Extract the active branch data
        branch_data = result.get("branch_data", {})
        active_branch = result.get("active_branch", "condfalse")

        # Store branch decision for downstream nodes that need it
        context.set_variable(f"branch[{node.id}]", active_branch)  # e.g., "condtrue" | "condfalse"

        # Return envelope with just the branch data using auto-detection
        # The actual branch routing is handled by emitting on the correct port
        output = EnvelopeFactory.create(
            body=branch_data if branch_data is not None else "",  # Natural data output
            produced_by=str(node.id),
            trace_id=request.execution_id or "",
        )

        # Store the branch decision for post_execute to use via handler state
        request.set_handler_state("active_branch", active_branch)

        return output

    def post_execute(self, request: ExecutionRequest[ConditionNode], output: Envelope) -> Envelope:
        """Post-execution hook to emit tokens on the correct branch.

        Only emits token on the active branch port to avoid confusion in TokenManager.
        TokenManager will match these ports to edges with matching source_output.
        """
        # Use the branch decision from handler state
        active_branch = request.get_handler_state("active_branch", "condfalse")

        # Emit output ONLY on the active branch port
        # This ensures TokenManager correctly tracks which branch was taken
        context = request.context
        node_id = request.node.id
        outputs = {active_branch: output}
        context.emit_outputs_as_tokens(node_id, outputs)

        return output

    async def on_error(
        self, request: ExecutionRequest[ConditionNode], error: Exception
    ) -> Envelope | None:
        # Return error envelope - condition defaults to false on error
        return EnvelopeFactory.create(
            body=str(error),
            produced_by=request.node.id,
            trace_id=request.execution_id or "",
            meta={"error_type": error.__class__.__name__, "is_error": True},
        )
