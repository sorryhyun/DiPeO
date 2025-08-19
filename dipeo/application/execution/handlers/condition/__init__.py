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
        
        # Execute evaluation with pre-selected evaluator
        eval_result = await evaluator.evaluate(node, context, diagram, legacy_inputs)
        result = eval_result["result"]
        output_value = eval_result["output_data"] or {}
        
        # Store evaluation metadata in instance variable for later use
        self._current_evaluation_metadata = eval_result["metadata"]
        
        true_output = output_value.get("condtrue") if result else None
        false_output = output_value.get("condfalse") if not result else None
        
        logger.debug(
            f"ConditionNode {node.id}: type={node.condition_type}, "
            f"result={result}, has_true_output={true_output is not None}, "
            f"has_false_output={false_output is not None}"
        )
        
        # Return structured result for serialization
        return {
            "result": result,
            "condtrue": true_output,
            "condfalse": false_output,
            "active_branch": "condtrue" if result else "condfalse",
            "condition_type": node.condition_type,
            "evaluation_metadata": self._current_evaluation_metadata,
            "timestamp": time.time()
        }

    def serialize_output(
        self,
        result: Any,
        request: ExecutionRequest[ConditionNode]
    ) -> Envelope:
        """Serialize condition result to special condition envelope."""
        node = request.node
        
        # Extract result data
        condition_result = result["result"]
        meta = {k: v for k, v in result.items() if k != "result"}
        
        # Create Envelope directly for proper branch routing
        from dipeo.domain.execution.envelope import Envelope
        
        output = Envelope(
            content_type="condition_result",  # Special content type for conditions
            body=condition_result,
            produced_by=str(node.id),
            meta=meta
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