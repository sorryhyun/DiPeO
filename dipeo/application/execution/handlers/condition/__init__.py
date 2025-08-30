"""Refactored condition node handler using evaluator pattern."""

import json
import logging
import time
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import DIAGRAM
from dipeo.diagram_generated.generated_nodes import ConditionNode, NodeType
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.condition_model import ConditionNodeData

from .evaluators import (
    ConditionEvaluator,
    CustomExpressionEvaluator,
    MaxIterationsEvaluator,
    NodesExecutedEvaluator,
)

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
        }
        # Instance variables for passing data between methods
        self._current_evaluator = None
        self._current_diagram = None

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
        return ["diagram"]

    @property
    def description(self) -> str:
        return "Evaluates conditions using specialized evaluators for different condition types"
    
    def validate(self, request: ExecutionRequest[ConditionNode]) -> Optional[str]:
        if not request.get_service(DIAGRAM.name):
            return "Diagram service not available"
        
        node = request.node
        condition_type = node.condition_type
        
        if condition_type not in self._evaluators:
            supported = ", ".join(self._evaluators.keys())
            return f"Unsupported condition type: {condition_type}. Supported types: {supported}"
        
        if condition_type == "custom" and not node.expression:
            return "Custom condition requires an expression"
        
        if condition_type == "check_nodes_executed" and not node.node_indices:
            return "check_nodes_executed requires node_indices"
            
        return None
    
    async def pre_execute(self, request: ExecutionRequest[ConditionNode]) -> Optional[Envelope]:
        """Pre-execution setup: validate services and select evaluator.
        
        Moves evaluator selection and service validation out of execute_request
        for cleaner separation of concerns.
        """
        node = request.node
        condition_type = node.condition_type
        
        # Validate diagram service is available
        diagram = request.get_service(DIAGRAM.name)
        if not diagram:
            return EnvelopeFactory.error(
                "Diagram service not available",
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
        
        # Store evaluator and diagram in instance variables for execute_request
        self._current_evaluator = evaluator
        self._current_diagram = diagram
        
        # No early return - proceed to execute_request
        return None
    
    async def run(
        self,
        inputs: dict[str, Any],
        request: ExecutionRequest[ConditionNode]
    ) -> dict[str, Any]:
        """Execute condition evaluation."""
        node = request.node
        context = request.context
        legacy_inputs = inputs
        
        # Use evaluator and diagram from instance variables (set in pre_execute)
        evaluator = self._current_evaluator
        diagram = self._current_diagram
        
        # Track and expose loop index if configured
        if hasattr(node, 'expose_index_as') and node.expose_index_as:
            # Get execution count for loop index (0-based)
            execution_count = context.get_node_execution_count(node.id)
            loop_index = execution_count - 1  # Convert to 0-based index
            
            # Store in variables for downstream nodes to access (persisted across executions)
            context.set_variable(node.expose_index_as, loop_index)
            
            logger.debug(
                f"ConditionNode {node.id}: Exposing loop index as '{node.expose_index_as}' = {loop_index}"
            )
        
        # Execute evaluation with pre-selected evaluator
        eval_result = await evaluator.evaluate(node, context, diagram, legacy_inputs)
        result = eval_result["result"]
        output_value = eval_result["output_data"] or {}
        
        # Store evaluation metadata in instance variable for later use
        self._current_evaluation_metadata = eval_result["metadata"]
        
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