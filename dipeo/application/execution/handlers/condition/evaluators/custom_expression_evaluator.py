"""Evaluator for custom expression conditions."""

import json
import logging
from typing import Any

from .expression_evaluator import ConditionEvaluator as ExpressionEvaluator
from dipeo.domain.execution.execution_context import ExecutionContext
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.diagram_generated.generated_nodes import ConditionNode

from .base import BaseConditionEvaluator, EvaluationResult

logger = logging.getLogger(__name__)


class CustomExpressionEvaluator(BaseConditionEvaluator):
    """Evaluates custom expressions using safe AST evaluation."""
    
    def __init__(self):
        self._expression_evaluator = ExpressionEvaluator()
    
    async def evaluate(
        self,
        node: ConditionNode,
        context: ExecutionContext,
        diagram: ExecutableDiagram,
        inputs: dict[str, Any]
    ) -> EvaluationResult:
        expression = node.expression or ""
        
        if not expression:
            return EvaluationResult(
                result=False,
                metadata={"reason": "No expression provided"},
                output_data=inputs if inputs else {}
            )
        
        eval_context = inputs.copy() if inputs else {}
        
        # Add exposed loop indices to evaluation context
        metadata = context.get_execution_metadata()
        for key, value in metadata.items():
            if key.startswith("loop_index_"):
                var_name = key.replace("loop_index_", "")
                eval_context[var_name] = value
        
        result = self._expression_evaluator.evaluate_custom_expression(
            expression=expression,
            context_values=eval_context
        )
        
        # Pass through inputs directly without wrapping
        output_data = inputs if inputs else {}

        return EvaluationResult(
            result=result,
            metadata={
                "expression": expression,
                "context_keys": list(eval_context.keys()) if eval_context else []
            },
            output_data=output_data
        )