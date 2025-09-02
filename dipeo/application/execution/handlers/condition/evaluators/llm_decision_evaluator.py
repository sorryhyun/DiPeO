"""Evaluator for LLM-based decision conditions."""

import logging
from typing import Any

from dipeo.domain.execution.execution_context import ExecutionContext
from dipeo.diagram_generated.generated_nodes import ConditionNode
from dipeo.infrastructure.llm.adapters import LLMDecisionAdapter

from .base import BaseConditionEvaluator, EvaluationResult

logger = logging.getLogger(__name__)


class LLMDecisionEvaluator(BaseConditionEvaluator):
    """Evaluator that uses LLM to make binary decisions."""
    
    def __init__(self):
        """Initialize the LLM decision evaluator."""
        super().__init__()
        # Services will be set by the handler
        self._decision_adapter = None
        self._orchestrator = None
        self._prompt_builder = None
    
    def set_services(self, orchestrator, prompt_builder):
        """Set services for the evaluator to use."""
        self._orchestrator = orchestrator
        self._prompt_builder = prompt_builder
        # Initialize the decision adapter with the orchestrator
        self._decision_adapter = LLMDecisionAdapter(orchestrator)
    
    async def evaluate(
        self,
        node: ConditionNode,
        context: ExecutionContext,
        inputs: dict[str, Any]
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
            return EvaluationResult(
                result=False,
                metadata={"error": "Orchestrator service not available"},
                output_data=inputs
            )
        
        if not self._decision_adapter:
            logger.error("Decision adapter not available for LLM decision")
            return EvaluationResult(
                result=False,
                metadata={"error": "Decision adapter not available"},
                output_data=inputs
            )
        
        # Get person configuration
        person_id = getattr(node, 'person', None)
        if not person_id:
            logger.error("No person specified for LLM decision")
            return EvaluationResult(
                result=False,
                metadata={"error": "No person specified"},
                output_data=inputs
            )
        
        # Get prompt
        # Access diagram through context
        prompt = self._orchestrator.load_prompt(
            prompt_file=getattr(node, 'judge_by_file', None),
            inline_prompt=getattr(node, 'judge_by', None),
            diagram=context.diagram,
            node_label=str(node.id)
        )
        
        if not prompt:
            logger.error("No prompt specified (neither judge_by nor judge_by_file)")
            return EvaluationResult(
                result=False,
                metadata={"error": "No prompt specified"},
                output_data=inputs
            )
        
        # Build template values from inputs and context
        template_values = inputs.copy() if inputs else {}
        
        # Add variables from context
        if hasattr(context, 'get_variables'):
            variables = context.get_variables()
            template_values.update(variables)
        
        # Build template
        if self._prompt_builder:
            try:
                prompt = self._prompt_builder.build(prompt, template_values)
            except Exception as e:
                logger.warning(f"Failed to process prompt template: {e}. Using raw prompt.")
        
        # Use the adapter to make the decision
        try:
            decision, metadata = await self._decision_adapter.make_decision(
                person_id=person_id,
                prompt=prompt,
                template_values=template_values,
                memory_profile=getattr(node, 'memorize_to', 'GOLDFISH'),
                diagram=context.diagram
            )
            
            # Update metadata with node-specific information
            metadata.update({
                "memorize_to": getattr(node, 'memorize_to', 'GOLDFISH'),
                "prompt_preview": prompt[:200],
            })
            
            return EvaluationResult(
                result=decision,
                metadata=metadata,
                output_data=inputs
            )
            
        except Exception as e:
            logger.error(f"LLM decision execution failed: {e}")
            return EvaluationResult(
                result=False,
                metadata={"error": str(e)},
                output_data=inputs
            )