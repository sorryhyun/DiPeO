"""Refactored condition node handler using evaluator pattern."""

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import EnvelopeNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import DIAGRAM
from dipeo.diagram_generated.generated_nodes import ConditionNode, NodeType
from dipeo.core.execution.node_output import ConditionOutput, ErrorOutput, NodeOutputProtocol
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.condition_model import ConditionNodeData

from .evaluators import (
    ConditionEvaluator,
    CustomExpressionEvaluator,
    MaxIterationsEvaluator,
    NodesExecutedEvaluator,
)

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


@register_handler
class ConditionNodeHandler(EnvelopeNodeHandler[ConditionNode]):
    """Handler for condition nodes using evaluator pattern with envelope support."""
    
    # Enable envelope mode
    _expects_envelopes = True
    
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
    
    async def pre_execute(self, request: ExecutionRequest[ConditionNode]) -> Optional[NodeOutputProtocol]:
        """Pre-execution setup: validate services and select evaluator.
        
        Moves evaluator selection and service validation out of execute_request
        for cleaner separation of concerns.
        """
        node = request.node
        condition_type = node.condition_type
        
        # Validate diagram service is available
        diagram = request.get_service(DIAGRAM.name)
        if not diagram:
            return self.create_error_output(
                ValueError("Diagram service not available"),
                node.id,
                request.execution_id or ""
            )
        
        # Select and validate evaluator
        evaluator = self._evaluators.get(condition_type)
        if not evaluator:
            logger.error(f"No evaluator found for condition type: {condition_type}")
            return self.create_error_output(
                ValueError(f"No evaluator for condition type: {condition_type}"),
                node.id,
                request.execution_id or ""
            )
        
        # Store evaluator and diagram in instance variables for execute_request
        self._current_evaluator = evaluator
        self._current_diagram = diagram
        
        # No early return - proceed to execute_request
        return None
    
    async def execute_with_envelopes(
        self,
        request: ExecutionRequest[ConditionNode],
        inputs: dict[str, Envelope]
    ) -> NodeOutputProtocol:
        """Execute condition evaluation with envelope inputs."""
        node = request.node
        context = request.context
        trace_id = request.execution_id or ""
        
        # Convert envelopes to legacy inputs for evaluators
        legacy_inputs = {}
        for key, envelope in inputs.items():
            if envelope.content_type == "raw_text":
                legacy_inputs[key] = self.reader.as_text(envelope)
            elif envelope.content_type == "object":
                legacy_inputs[key] = self.reader.as_json(envelope)
            else:
                legacy_inputs[key] = envelope.body
        
        # Use evaluator and diagram from instance variables (set in pre_execute)
        evaluator = self._current_evaluator
        diagram = self._current_diagram
        
        # Execute evaluation with pre-selected evaluator
        eval_result = await evaluator.evaluate(node, context, diagram, legacy_inputs)
        result = eval_result["result"]
        output_value = eval_result["output_data"] or {}
        
        # Store evaluation metadata in instance variable instead of request.metadata
        self._current_evaluation_metadata = eval_result["metadata"]
        
        true_output = output_value.get("condtrue") if result else None
        false_output = output_value.get("condfalse") if not result else None
        
        logger.debug(
            f"ConditionNode {node.id}: type={node.condition_type}, "
            f"result={result}, has_true_output={true_output is not None}, "
            f"has_false_output={false_output is not None}"
        )
        
        # Create output envelope with condition result
        # The envelope needs special metadata for the StandardRuntimeResolver to handle
        from dataclasses import replace
        
        output_envelope = EnvelopeFactory.json(
            {
                "result": result,
                "true_output": true_output,
                "false_output": false_output,
                "condition_type": node.condition_type,
                "evaluation_metadata": self._current_evaluation_metadata
            },
            produced_by=node.id,
            trace_id=trace_id
        ).with_meta(
            condition_type=node.condition_type,
            result=result,
            # Add branch metadata for runtime resolver
            branch_taken="true" if result else "false",
            branch_data=true_output if result else false_output
        )
        
        # Update content type to condition_result for proper handling
        output_envelope = replace(output_envelope, content_type="condition_result")
        
        return self.create_success_output(output_envelope)
    
    def post_execute(
        self,
        request: ExecutionRequest[ConditionNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
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
    ) -> NodeOutputProtocol | None:
        # Return error envelope - condition defaults to false on error
        return self.create_error_output(
            error,
            request.node.id,
            request.execution_id or ""
        )