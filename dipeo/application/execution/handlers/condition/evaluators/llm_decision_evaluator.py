"""Evaluator for LLM-based decision conditions."""

import logging
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.condition_node import ConditionNode
from dipeo.domain.execution.execution_context import ExecutionContext

from .base import BaseConditionEvaluator, EvaluationResult

logger = get_module_logger(__name__)


class LLMDecisionEvaluator(BaseConditionEvaluator):
    """Evaluator that uses LLM to make binary decisions."""

    def __init__(self):
        super().__init__()
        self._orchestrator = None
        self._prompt_builder = None

    def set_services(self, orchestrator, prompt_builder):
        self._orchestrator = orchestrator
        self._prompt_builder = prompt_builder

    def _add_loop_index_to_output(
        self, node: ConditionNode, context: ExecutionContext, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        output_data = inputs if inputs else {}
        if (
            hasattr(node, "expose_index_as")
            and node.expose_index_as
            and hasattr(context, "get_variable")
        ):
            loop_value = context.get_variable(node.expose_index_as)
            if loop_value is not None:
                output_data[node.expose_index_as] = loop_value
        return output_data

    async def evaluate(
        self, node: ConditionNode, context: ExecutionContext, inputs: dict[str, Any]
    ) -> EvaluationResult:
        if not self._orchestrator:
            logger.error("Orchestrator service not available for LLM decision")
            return EvaluationResult(
                result=False,
                metadata={"error": "Orchestrator service not available"},
                output_data=self._add_loop_index_to_output(node, context, inputs),
            )

        person_id = getattr(node, "person", None)
        if not person_id:
            logger.error("No person specified for LLM decision")
            return EvaluationResult(
                result=False,
                metadata={"error": "No person specified"},
                output_data=self._add_loop_index_to_output(node, context, inputs),
            )

        prompt = self._orchestrator.load_prompt(
            prompt_file=getattr(node, "judge_by_file", None),
            inline_prompt=getattr(node, "judge_by", None),
            diagram=context.diagram,
            node_label=str(node.id),
        )

        if not prompt:
            logger.error("No prompt specified (neither judge_by nor judge_by_file)")
            return EvaluationResult(
                result=False,
                metadata={"error": "No prompt specified"},
                output_data=self._add_loop_index_to_output(node, context, inputs),
            )

        template_values = inputs.copy() if inputs else {}

        if hasattr(context, "get_variables"):
            variables = context.get_variables()
            template_values.update(variables)

        if self._prompt_builder:
            try:
                prompt = self._prompt_builder.build(prompt, template_values)
            except Exception as e:
                logger.warning(f"Failed to process prompt template: {e}. Using raw prompt.")

        try:
            decision, metadata = await self._orchestrator.make_llm_decision(
                person_id=person_id,
                prompt=prompt,
                template_values=template_values,
                memory_profile=getattr(node, "memorize_to", "GOLDFISH"),
                diagram=context.diagram,
            )

            metadata.update(
                {
                    "memorize_to": getattr(node, "memorize_to", "GOLDFISH"),
                    "prompt_preview": prompt[:200],
                }
            )

            output_data = self._add_loop_index_to_output(node, context, inputs)
            return EvaluationResult(result=decision, metadata=metadata, output_data=output_data)

        except Exception as e:
            logger.error(f"LLM decision execution failed: {e}")
            return EvaluationResult(
                result=False,
                metadata={"error": str(e)},
                output_data=self._add_loop_index_to_output(node, context, inputs),
            )
