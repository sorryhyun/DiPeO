"""Evaluator for custom expression conditions."""

from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.condition_node import ConditionNode
from dipeo.domain.execution.context.execution_context import ExecutionContext

from .base import BaseConditionEvaluator, EvaluationResult
from .expression_evaluator import ConditionEvaluator as ExpressionEvaluator

logger = get_module_logger(__name__)


class CustomExpressionEvaluator(BaseConditionEvaluator):
    def __init__(self) -> None:
        self._expression_evaluator = ExpressionEvaluator()

    async def evaluate(
        self, node: ConditionNode, context: ExecutionContext, inputs: dict[str, Any]
    ) -> EvaluationResult:
        expression = node.expression or ""

        if not expression:
            return EvaluationResult(
                result=False,
                metadata={"reason": "No expression provided"},
                output_data=inputs if inputs else {},
            )

        eval_context = inputs.copy() if inputs else {}

        if hasattr(context, "get_variables"):
            eval_context.update(context.get_variables())

        result = self._expression_evaluator.evaluate_custom_expression(
            expression=expression, context_values=eval_context
        )

        return EvaluationResult(
            result=result,
            metadata={
                "expression": expression,
                "context_keys": list(eval_context.keys()),
            },
            output_data=inputs if inputs else {},
        )
