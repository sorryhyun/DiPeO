"""Evaluator for checking if specific nodes have been executed."""

from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.condition_node import ConditionNode
from dipeo.domain.execution.context.execution_context import ExecutionContext

from .base import BaseConditionEvaluator, EvaluationResult
from .expression_evaluator import ConditionEvaluator as EvaluationService

logger = get_module_logger(__name__)


class NodesExecutedEvaluator(BaseConditionEvaluator):
    """Evaluates whether specific nodes have been executed."""

    def __init__(self):
        self._evaluation_service = EvaluationService()

    async def evaluate(
        self, node: ConditionNode, context: ExecutionContext, inputs: dict[str, Any]
    ) -> EvaluationResult:
        target_nodes = node.node_indices or []

        if not target_nodes:
            return EvaluationResult(
                result=False,
                metadata={"reason": "No target nodes specified"},
                output_data=inputs if inputs else {},
            )

        node_outputs = self.extract_node_outputs(context)

        result = self._evaluation_service.check_nodes_executed(
            target_node_ids=target_nodes, node_outputs=node_outputs
        )

        output_data = inputs if inputs else {}

        if (
            hasattr(node, "expose_index_as")
            and node.expose_index_as
            and hasattr(context, "get_variable")
        ):
            loop_value = context.get_variable(node.expose_index_as)
            if loop_value is not None:
                output_data[node.expose_index_as] = loop_value

        logger.debug(
            f"NodesExecutedEvaluator: target_nodes={target_nodes}, "
            f"executed_nodes={list(node_outputs.keys())}, result={result}"
        )

        return EvaluationResult(
            result=result,
            metadata={"target_nodes": target_nodes, "executed_nodes": list(node_outputs.keys())},
            output_data=output_data,
        )
