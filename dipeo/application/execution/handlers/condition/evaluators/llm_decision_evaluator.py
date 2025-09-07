"""Evaluator for LLM-based decision conditions."""

import logging
from typing import Any

from dipeo.diagram_generated.unified_nodes.condition_node import ConditionNode
from dipeo.domain.execution.execution_context import ExecutionContext

from .base import BaseConditionEvaluator, EvaluationResult

logger = logging.getLogger(__name__)


class LLMDecisionEvaluator(BaseConditionEvaluator):
    """Evaluator that uses LLM to make binary decisions."""

    def __init__(self):
        """Initialize the LLM decision evaluator."""
        super().__init__()
        # Services will be set by the handler
        self._orchestrator = None
        self._prompt_builder = None

    def set_services(self, orchestrator, prompt_builder):
        """Set services for the evaluator to use."""
        self._orchestrator = orchestrator
        self._prompt_builder = prompt_builder

    async def evaluate(
        self, node: ConditionNode, context: ExecutionContext, inputs: dict[str, Any]
    ) -> EvaluationResult:
        """Evaluate a condition using LLM to make a binary decision.

        Args:
            node: The condition node with LLM configuration
            context: Execution context (contains diagram)
            inputs: Input data from connections

        Returns:
            EvaluationResult with boolean decision and metadata
        """
        if not self._orchestrator:
            logger.error("Orchestrator service not available for LLM decision")
            # Include exposed loop index even in error cases
            output_data = inputs if inputs else {}
            if (
                hasattr(node, "expose_index_as")
                and node.expose_index_as
                and hasattr(context, "get_variable")
            ):
                loop_value = context.get_variable(node.expose_index_as)
                if loop_value is not None:
                    output_data[node.expose_index_as] = loop_value
            return EvaluationResult(
                result=False,
                metadata={"error": "Orchestrator service not available"},
                output_data=output_data,
            )

        # Get person configuration
        person_id = getattr(node, "person", None)
        if not person_id:
            logger.error("No person specified for LLM decision")
            # Include exposed loop index even in error cases
            output_data = inputs if inputs else {}
            if (
                hasattr(node, "expose_index_as")
                and node.expose_index_as
                and hasattr(context, "get_variable")
            ):
                loop_value = context.get_variable(node.expose_index_as)
                if loop_value is not None:
                    output_data[node.expose_index_as] = loop_value
            return EvaluationResult(
                result=False, metadata={"error": "No person specified"}, output_data=output_data
            )

        # Get prompt
        # Access diagram through context
        prompt = self._orchestrator.load_prompt(
            prompt_file=getattr(node, "judge_by_file", None),
            inline_prompt=getattr(node, "judge_by", None),
            diagram=context.diagram,
            node_label=str(node.id),
        )

        if not prompt:
            logger.error("No prompt specified (neither judge_by nor judge_by_file)")
            # Include exposed loop index even in error cases
            output_data = inputs if inputs else {}
            if (
                hasattr(node, "expose_index_as")
                and node.expose_index_as
                and hasattr(context, "get_variable")
            ):
                loop_value = context.get_variable(node.expose_index_as)
                if loop_value is not None:
                    output_data[node.expose_index_as] = loop_value
            return EvaluationResult(
                result=False, metadata={"error": "No prompt specified"}, output_data=output_data
            )

        # Build template values from inputs and context
        template_values = inputs.copy() if inputs else {}

        # Add variables from context
        if hasattr(context, "get_variables"):
            variables = context.get_variables()
            template_values.update(variables)

        # Build template
        if self._prompt_builder:
            try:
                prompt = self._prompt_builder.build(prompt, template_values)
            except Exception as e:
                logger.warning(f"Failed to process prompt template: {e}. Using raw prompt.")

        # Use the orchestrator to make the decision
        try:
            decision, metadata = await self._orchestrator.make_llm_decision(
                person_id=person_id,
                prompt=prompt,
                template_values=template_values,
                memory_profile=getattr(node, "memorize_to", "GOLDFISH"),
                diagram=context.diagram,
            )

            # Update metadata with node-specific information
            metadata.update(
                {
                    "memorize_to": getattr(node, "memorize_to", "GOLDFISH"),
                    "prompt_preview": prompt[:200],
                }
            )

            # Include exposed loop index in output data for downstream nodes
            output_data = inputs if inputs else {}
            if (
                hasattr(node, "expose_index_as")
                and node.expose_index_as
                and node.expose_index_as in template_values
            ):
                output_data[node.expose_index_as] = template_values[node.expose_index_as]

            return EvaluationResult(result=decision, metadata=metadata, output_data=output_data)

        except Exception as e:
            logger.error(f"LLM decision execution failed: {e}")
            # Include exposed loop index even in error cases
            output_data = inputs if inputs else {}
            if (
                hasattr(node, "expose_index_as")
                and node.expose_index_as
                and hasattr(context, "get_variable")
            ):
                loop_value = context.get_variable(node.expose_index_as)
                if loop_value is not None:
                    output_data[node.expose_index_as] = loop_value
            return EvaluationResult(
                result=False, metadata={"error": str(e)}, output_data=output_data
            )
