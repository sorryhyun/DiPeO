"""Refactored condition node handler using evaluator pattern."""

import json
import logging
import time
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.diagram_generated.generated_nodes import ConditionNode, NodeType
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.condition_model import ConditionNodeData

from .evaluators import (
    ConditionEvaluator,
    CustomExpressionEvaluator,
    MaxIterationsEvaluator,
    NodesExecutedEvaluator,
)
from .evaluators.llm_decision_evaluator import LLMDecisionEvaluator

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


@register_handler
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
        # Instance variables for passing data between methods
        self._current_evaluator = None

    @property
    def node_class(self) -> type[ConditionNode]:
        return ConditionNode
    
    @property
    def node_type(self) -> str:
        return NodeType.CONDITION.value

    @property
    def schema(self) -> type[BaseModel]:
        return ConditionNodeData

    @property
    def requires_services(self) -> list[str]:
        return [
            "execution_orchestrator",
            "prompt_builder"
        ]

    @property
    def description(self) -> str:
        return "Evaluates conditions using specialized evaluators for different condition types"
    
    def validate(self, request: ExecutionRequest[ConditionNode]) -> Optional[str]:
        if not request.context or not hasattr(request.context, 'diagram'):
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
            if not hasattr(node, 'person') or not node.person:
                return "llm_decision requires a person to be specified"
            if not hasattr(node, 'judge_by') and not hasattr(node, 'judge_by_file'):
                return "llm_decision requires either judge_by or judge_by_file"
            
        return None
    
    async def pre_execute(self, request: ExecutionRequest[ConditionNode]) -> Optional[Envelope]:
        """Pre-execution setup: validate services and select evaluator.
        
        Moves evaluator selection and service validation out of execute_request
        for cleaner separation of concerns.
        """
        node = request.node
        condition_type = node.condition_type
        
        # Get the currently executing diagram from the context
        diagram = request.context.diagram if request.context else None
        if diagram is None:
            return EnvelopeFactory.error(
                "Executable diagram not available in context",
                error_type="ValueError",
                produced_by=node.id,
                trace_id=request.execution_id or ""
            )
        
        # Select and validate evaluator
        evaluator = self._evaluators.get(condition_type)
        if not evaluator:
            logger.error(f"No evaluator found for condition type: {condition_type}")
            return EnvelopeFactory.error(
                f"No evaluator for condition type: {condition_type}",
                error_type="ValueError",
                produced_by=node.id,
                trace_id=request.execution_id or ""
            )
        
        # Store evaluator in instance variable for execute_request
        self._current_evaluator = evaluator
        
        # No early return - proceed to execute_request
        return None
    
    async def prepare_inputs(
        self,
        request: ExecutionRequest[ConditionNode],
        inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare inputs with token consumption.
        
        Phase 5: Now consumes tokens from incoming edges when available.
        """
        # Phase 5: Consume tokens from incoming edges or fall back to regular inputs
        envelope_inputs = self.consume_token_inputs(request, inputs)
        
        # Call parent prepare_inputs for default envelope conversion
        return await super().prepare_inputs(request, envelope_inputs)
    
    async def run(
        self,
        inputs: dict[str, Any],
        request: ExecutionRequest[ConditionNode]
    ) -> dict[str, Any]:
        """Execute condition evaluation."""
        node = request.node
        context = request.context
        legacy_inputs = inputs
        
        # Use evaluator from instance variable (set in pre_execute)
        evaluator = self._current_evaluator
        
        # For LLM decision evaluator, pass required services
        if node.condition_type == "llm_decision" and hasattr(evaluator, 'set_services'):
            evaluator.set_services(
                orchestrator=request.get_service("execution_orchestrator"),
                prompt_builder=request.get_service("prompt_builder")
            )
        
        # Track and expose loop index if configured
        if hasattr(node, 'expose_index_as') and node.expose_index_as:
            # Use the exposed variable directly - it persists across executions
            # and only gets incremented when we complete a full loop iteration
            current_loop_index = context.get_variable(node.expose_index_as)
            
            # Initialize on first execution
            if current_loop_index is None:
                current_loop_index = 0
                context.set_variable(node.expose_index_as, current_loop_index)
            
            logger.debug(
                f"ConditionNode {node.id}: Exposing loop index as '{node.expose_index_as}' = {current_loop_index}"
            )
        
        # Execute evaluation with pre-selected evaluator
        eval_result = await evaluator.evaluate(node, context, legacy_inputs)
        result = eval_result["result"]
        output_value = eval_result["output_data"] or {}
        
        # Store evaluation metadata in instance variable for later use
        self._current_evaluation_metadata = eval_result["metadata"]
        
        # Increment loop index when condition is FALSE and we have a loop-back edge
        # This happens when we're continuing the loop to the next iteration
        if hasattr(node, 'expose_index_as') and node.expose_index_as and not result:
            # Check if the false branch loops back (has edges going to earlier nodes)
            has_loop_back = False
            outgoing_edges = context.diagram.get_outgoing_edges(node.id)
            for edge in outgoing_edges:
                # Check if this is the false branch edge
                if str(getattr(edge, 'source_output', '')).lower() == 'condfalse':
                    target_node = context.diagram.get_node(edge.target_node_id)
                    # If target has been executed before, it's likely a loop-back
                    if target_node and context.get_node_execution_count(edge.target_node_id) > 0:
                        has_loop_back = True
                        break
            
            # Only increment if we're actually looping back AND we haven't already incremented
            # for this execution count (prevents duplicate increments on resets)
            if has_loop_back:
                current_loop_index = context.get_variable(node.expose_index_as)
                last_increment_at = context.get_variable(f"{node.expose_index_as}_last_increment_at")
                current_exec_count = context.get_node_execution_count(node.id)
                
                # Only increment if we haven't already incremented at this execution count
                if last_increment_at != current_exec_count:
                    new_index = current_loop_index + 1
                    context.set_variable(node.expose_index_as, new_index)
                    context.set_variable(f"{node.expose_index_as}_last_increment_at", current_exec_count)
                    logger.debug(
                        f"ConditionNode {node.id}: Incremented loop index to {new_index} (loop continuation)"
                    )
                else:
                    logger.debug(
                        f"ConditionNode {node.id}: Skipping increment - already incremented at execution count {current_exec_count}"
                    )
        
        # Return only the active branch data
        active_branch = "condtrue" if result else "condfalse"
        
        # Return structured result for serialization
        # The output_value goes directly in the response, not wrapped
        return {
            "result": result,
            "active_branch": active_branch,
            "branch_data": output_value,  # Direct pass-through of active branch data
            "condition_type": node.condition_type,
            "evaluation_metadata": self._current_evaluation_metadata,
            "timestamp": time.time()
        }

    def serialize_output(
        self,
        result: Any,
        request: ExecutionRequest[ConditionNode]
    ) -> Envelope:
        """Serialize condition result to envelope with active branch data in body."""
        node = request.node
        context = request.context
        
        # Extract the active branch data
        branch_data = result.get("branch_data", {})
        active_branch = result.get("active_branch", "condfalse")
        
        # 1) Publish globals for any downstream node/template
        context.set_variable(f"branch[{node.id}]", active_branch)  # e.g., "condtrue" | "condfalse"
        
        # 2) Return a normal envelope (no special content_type)
        if isinstance(branch_data, dict):
            output = EnvelopeFactory.json(
                branch_data,
                produced_by=str(node.id),
                trace_id=request.execution_id or ""
            )
        else:
            output = EnvelopeFactory.text(
                str(branch_data) if branch_data is not None else "",
                produced_by=str(node.id),
                trace_id=request.execution_id or ""
            )
        
        return output
    
    def post_execute(
        self,
        request: ExecutionRequest[ConditionNode],
        output: Envelope
    ) -> Envelope:
        """Post-execution hook to emit tokens with conditional filtering.
        
        Phase 5: Now emits output as tokens to trigger downstream nodes.
        Condition nodes use emit_outputs_as_tokens which handles conditional branch filtering.
        """
        # Phase 5: Emit output as tokens to trigger downstream nodes
        # emit_token_outputs will automatically handle conditional branch filtering
        self.emit_token_outputs(request, output)
        
        # Debug logging without using request.metadata
        condition_type = request.node.condition_type
        result = output.value if hasattr(output, 'value') else None
        print(f"[ConditionNode] Evaluated {condition_type} condition - Result: {result}")
        
        if self._current_evaluation_metadata:
            print(f"[ConditionNode] Evaluation details: {self._current_evaluation_metadata}")
        
        return output
    
    async def on_error(
        self,
        request: ExecutionRequest[ConditionNode],
        error: Exception
    ) -> Envelope | None:
        # Return error envelope - condition defaults to false on error
        return EnvelopeFactory.error(
            str(error),
            error_type=error.__class__.__name__,
            produced_by=request.node.id,
            trace_id=request.execution_id or ""
        )