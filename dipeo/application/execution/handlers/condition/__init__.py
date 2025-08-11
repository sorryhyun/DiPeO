"""Refactored condition node handler using evaluator pattern."""

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import DIAGRAM
from dipeo.diagram_generated.generated_nodes import ConditionNode, NodeType
from dipeo.core.execution.node_output import ConditionOutput, NodeOutputProtocol
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
class ConditionNodeHandler(TypedNodeHandler[ConditionNode]):
    """Handler for condition nodes using evaluator pattern."""
    
    def __init__(self):
        self._evaluators: dict[str, ConditionEvaluator] = {
            "detect_max_iterations": MaxIterationsEvaluator(),
            "check_nodes_executed": NodesExecutedEvaluator(),
            "custom": CustomExpressionEvaluator(),
        }

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
    
    async def execute_request(self, request: ExecutionRequest[ConditionNode]) -> NodeOutputProtocol:
        node = request.node
        context = request.context
        inputs = request.inputs
        
        diagram = request.get_service(DIAGRAM.name)
        if not diagram:
            raise ValueError("Diagram service not available")
        
        condition_type = node.condition_type
        evaluator = self._evaluators.get(condition_type)
        
        if not evaluator:
            logger.error(f"No evaluator found for condition type: {condition_type}")
            result = False
            output_value = {"condfalse": inputs if inputs else {}}
        else:
            eval_result = await evaluator.evaluate(node, context, diagram, inputs)
            result = eval_result["result"]
            output_value = eval_result["output_data"] or {}
            
            request.add_metadata("evaluation_metadata", eval_result["metadata"])
        
        true_output = output_value.get("condtrue") if result else None
        false_output = output_value.get("condfalse") if not result else None
        
        logger.debug(
            f"ConditionNode {node.id}: type={condition_type}, "
            f"result={result}, has_true_output={true_output is not None}, "
            f"has_false_output={false_output is not None}"
        )
        
        output = ConditionOutput(
            value=result,
            node_id=node.id,
            true_output=true_output,
            false_output=false_output
        )
        # Set metadata as JSON string
        output.metadata = json.dumps({
            "condition_type": condition_type,
            "evaluation_metadata": request.metadata.get("evaluation_metadata", {})
        })
        return output
    
    def post_execute(
        self,
        request: ExecutionRequest[ConditionNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        if request.metadata.get("debug"):
            condition_type = request.node.condition_type
            result = output.value if hasattr(output, 'value') else None
            print(f"[ConditionNode] Evaluated {condition_type} condition - Result: {result}")
            
            eval_metadata = output.metadata.get("evaluation_metadata") if hasattr(output, 'metadata') else None
            if eval_metadata:
                print(f"[ConditionNode] Evaluation details: {eval_metadata}")
        
        return output
    
    async def on_error(
        self,
        request: ExecutionRequest[ConditionNode],
        error: Exception
    ) -> NodeOutputProtocol | None:
        condition_type = request.node.condition_type
        
        output = ConditionOutput(
            value=False,
            node_id=request.node.id,
            true_output=None,
            false_output=request.inputs if request.inputs else {}
        )
        # Set metadata as JSON string
        output.metadata = json.dumps({
            "condition_type": condition_type,
            "error": str(error),
            "error_type": type(error).__name__
        })
        return output