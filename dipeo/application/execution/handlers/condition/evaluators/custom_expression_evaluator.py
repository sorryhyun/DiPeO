"""Evaluator for custom expression conditions."""

import logging
from typing import Any

from dipeo.diagram_generated.generated_nodes import ConditionNode
from dipeo.domain.execution.execution_context import ExecutionContext

from .base import BaseConditionEvaluator, EvaluationResult
from .expression_evaluator import ConditionEvaluator as ExpressionEvaluator

logger = logging.getLogger(__name__)


class CustomExpressionEvaluator(BaseConditionEvaluator):
    """Evaluates custom expressions using safe AST evaluation."""

    def __init__(self):
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

        # Add all variables to evaluation context (includes loop indices)
        if hasattr(context, "get_variables"):
            variables = context.get_variables()
            for key, value in variables.items():
                # Variables take precedence over inputs
                eval_context[key] = value

        result = self._expression_evaluator.evaluate_custom_expression(
            expression=expression, context_values=eval_context
        )

        # Pass through inputs for downstream nodes
        output_data = inputs if inputs else {}

        # Note: expose_index_as variables are set globally by the condition handler
        # and should NOT be included in output_data to avoid conflicts

        return EvaluationResult(
            result=result,
            metadata={
                "expression": expression,
                "context_keys": list(eval_context.keys()) if eval_context else [],
            },
            output_data=output_data,
        )
