"""Evaluator for checking if specific nodes have been executed."""

import json
import logging
from typing import Any

from .expression_evaluator import ConditionEvaluator as EvaluationService
from dipeo.core.execution.execution_context import ExecutionContext
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.diagram_generated.generated_nodes import ConditionNode

from .base import BaseConditionEvaluator, EvaluationResult

logger = logging.getLogger(__name__)


class NodesExecutedEvaluator(BaseConditionEvaluator):
    """Evaluates whether specific nodes have been executed."""
    
    def __init__(self):
        self._evaluation_service = EvaluationService()
    
    async def evaluate(
        self,
        node: ConditionNode,
        context: ExecutionContext,
        diagram: ExecutableDiagram,
        inputs: dict[str, Any]
    ) -> EvaluationResult:
        """Check if target nodes have been executed."""
        target_nodes = node.node_indices or []
        
        if not target_nodes:
            return EvaluationResult(
                result=False,
                metadata={"reason": "No target nodes specified"},
                output_data={"condfalse": inputs if inputs else {}}
            )
        
        # Build node_outputs dict from context
        node_outputs = self.extract_node_outputs(context, diagram)
        
        # Check if nodes have been executed
        result = self._evaluation_service.check_nodes_executed(
            target_node_ids=target_nodes,
            node_outputs=node_outputs
        )
        
        # Prepare output data based on result
        if result:
            output_data = {"condtrue": inputs if inputs else {}}
        else:
            output_data = {"condfalse": inputs if inputs else {}}
        
        logger.debug(
            f"NodesExecutedEvaluator: target_nodes={target_nodes}, "
            f"executed_nodes={list(node_outputs.keys())}, result={result}"
        )
        
        return EvaluationResult(
            result=result,
            metadata={
                "target_nodes": target_nodes,
                "executed_nodes": list(node_outputs.keys())
            },
            output_data=output_data
        )