"""Evaluator for LLM-based decision conditions."""

import json
import logging
import re
from typing import Any, Optional

from dipeo.domain.conversation import Person
from dipeo.domain.execution.execution_context import ExecutionContext
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.diagram_generated.generated_nodes import ConditionNode
from dipeo.diagram_generated.domain_models import PersonID, PersonLLMConfig
from dipeo.config.llm import PERSON_JOB_TEMPERATURE, PERSON_JOB_MAX_TOKENS
from dipeo.application.execution.use_cases import PromptLoadingUseCase, PersonManagementUseCase
from dipeo.infrastructure.llm.core.types import ExecutionPhase

from .base import BaseConditionEvaluator, EvaluationResult

logger = logging.getLogger(__name__)


class LLMDecisionEvaluator(BaseConditionEvaluator):
    """Evaluator that uses LLM to make binary decisions."""
    
    def __init__(self):
        """Initialize the LLM decision evaluator."""
        super().__init__()
        # Services will be set by the handler
        self._llm_service = None
        self._conversation_manager = None
        self._prompt_builder = None
        self._filesystem_adapter = None
        self._diagram = None
        # Use cases for common operations
        self._prompt_loading_use_case = None
        self._person_management_use_case = PersonManagementUseCase()
    
    def set_services(self, llm_service, conversation_manager, prompt_builder, filesystem_adapter, diagram):
        """Set services for the evaluator to use."""
        self._llm_service = llm_service
        self._conversation_manager = conversation_manager
        self._prompt_builder = prompt_builder
        self._filesystem_adapter = filesystem_adapter
        self._diagram = diagram
        # Initialize prompt loading use case with filesystem adapter
        if filesystem_adapter:
            self._prompt_loading_use_case = PromptLoadingUseCase(filesystem_adapter)
    
    async def evaluate(
        self,
        node: ConditionNode,
        context: ExecutionContext,
        diagram: ExecutableDiagram,
        inputs: dict[str, Any]
    ) -> EvaluationResult:
        """Evaluate a condition using LLM to make a binary decision.
        
        Args:
            node: The condition node with LLM configuration
            context: Execution context
            diagram: The executable diagram
            inputs: Input data from connections
            
        Returns:
            EvaluationResult with boolean decision and metadata
        """
        # Use services set by handler
        llm_service = self._llm_service
        conversation_manager = self._conversation_manager
        prompt_builder = self._prompt_builder
        filesystem_adapter = self._filesystem_adapter
        
        if not llm_service:
            logger.error("LLM service not available for LLM decision")
            return EvaluationResult(
                result=False,
                metadata={"error": "LLM service not available"},
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
        
        # Get or create person using the use case
        person = self._person_management_use_case.get_or_create_person(
            person_id,
            diagram=self._diagram,
            conversation_manager=conversation_manager
        )
        if not person:
            logger.error(f"Could not find or create person: {person_id}")
            return EvaluationResult(
                result=False,
                metadata={"error": f"Person not found: {person_id}"},
                output_data=inputs
            )
        
        # Load prompt using the use case
        diagram_source_path = None
        if self._prompt_loading_use_case:
            diagram_source_path = self._prompt_loading_use_case.get_diagram_source_path(self._diagram)
        
        prompt_content = self._load_prompt(
            node,
            diagram_source_path
        )
        
        if not prompt_content:
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
        
        # Process template if prompt_builder is available
        if prompt_builder:
            try:
                # Use the build method which is the correct one for PromptBuilder
                processed_prompt = prompt_builder.build(
                    prompt_content,
                    template_values
                )
            except Exception as e:
                logger.warning(f"Failed to process prompt template: {e}. Using raw prompt.")
                processed_prompt = prompt_content
        else:
            processed_prompt = prompt_content
        
        # Get memory settings
        memorize_to = getattr(node, 'memorize_to', 'GOLDFISH')  # Default to GOLDFISH for fresh evaluation
        
        # For LLM decision mode, we typically want fresh evaluation without context
        # GOLDFISH mode is recommended to avoid bias from previous conversations
        if memorize_to and memorize_to.strip().upper() == "GOLDFISH":
            # Clear conversation for this person to ensure unbiased decision
            if hasattr(conversation_manager, 'clear_person_messages'):
                conversation_manager.clear_person_messages(person.id)
            person.reset_memory()
        
        # Execute LLM call with decision evaluation phase
        try:
            # Format messages: just the evaluation prompt as user message
            llm_messages = [
                {
                    "role": "user",
                    "content": processed_prompt
                }
            ]
            
            # Call LLM service with DECISION_EVALUATION phase
            # The adapter will inject the appropriate system prompt based on the phase
            result = await llm_service.complete(
                messages=llm_messages,
                model=person.llm_config.model,
                api_key_id=person.llm_config.api_key_id,
                service=person.llm_config.service,
                temperature=PERSON_JOB_TEMPERATURE,
                max_tokens=PERSON_JOB_MAX_TOKENS,
                execution_phase=ExecutionPhase.DECISION_EVALUATION  # This triggers the decision prompt
            )
            
            # Create response message for compatibility
            response_msg = None
            if result:
                from dipeo.diagram_generated import Message
                response_msg = Message(
                    from_person_id=person.id,
                    to_person_id=PersonID("system"),
                    content=result.text if result else "",
                    message_type="person_to_system"
                )
            
            # Parse response to extract boolean decision
            response_content = response_msg.content if response_msg else result.text if result else ""
            decision = self._parse_decision(response_content)
            
            logger.debug(f"LLM Decision - Prompt: {processed_prompt[:100]}...")
            logger.debug(f"LLM Decision - Response: {response_content[:200]}")
            logger.debug(f"LLM Decision - Parsed as: {decision}")
            
            return EvaluationResult(
                result=decision,
                metadata={
                    "person": str(person_id),
                    "memorize_to": memorize_to,
                    "prompt_preview": processed_prompt[:200],
                    "response_preview": response_content[:200],
                    "decision": decision
                },
                output_data=inputs
            )
            
        except Exception as e:
            logger.error(f"LLM execution failed: {e}")
            return EvaluationResult(
                result=False,
                metadata={"error": str(e)},
                output_data=inputs
            )
    
    def _load_prompt(
        self,
        node: ConditionNode,
        diagram_source_path: Optional[str] = None
    ) -> Optional[str]:
        """Load prompt from inline content or file.
        
        Args:
            node: The condition node
            diagram_source_path: Path to diagram source for relative resolution
            
        Returns:
            The prompt content
        """
        # Check inline prompt first
        prompt_content = getattr(node, 'judge_by', None)
        if prompt_content:
            return prompt_content
        
        # Try to load from file
        judge_by_file = getattr(node, 'judge_by_file', None)
        if judge_by_file and self._prompt_loading_use_case:
            return self._prompt_loading_use_case.load_prompt_file(
                judge_by_file,
                diagram_source_path,
                node_label=str(node.id)
            )
        
        return None
    
    
    
    def _parse_decision(self, response: str) -> bool:
        """Parse LLM response to extract boolean decision.
        
        Looks for affirmative/negative keywords to determine decision.
        """
        if not response:
            return False
        
        response_lower = response.lower().strip()
        
        # Remove any markdown or formatting
        response_lower = re.sub(r'[*_`#\[\]()]', '', response_lower)
        
        # Check for explicit YES/NO at the start
        if response_lower.startswith('yes'):
            return True
        if response_lower.startswith('no'):
            return False
        
        # Affirmative indicators
        affirmative_keywords = [
            'yes', 'true', 'valid', 'approved', 'approve', 
            'accept', 'accepted', 'correct', 'pass', 'passed',
            'good', 'ok', 'okay', 'proceed', 'continue',
            'affirmative', 'positive', 'success', 'successful'
        ]
        
        # Negative indicators
        negative_keywords = [
            'no', 'false', 'invalid', 'rejected', 'reject',
            'deny', 'denied', 'incorrect', 'fail', 'failed',
            'bad', 'not ok', 'not okay', 'stop', 'halt',
            'negative', 'unsuccessful', 'error', 'wrong'
        ]
        
        # Count occurrences
        affirmative_count = sum(1 for keyword in affirmative_keywords if keyword in response_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in response_lower)
        
        # Decision based on which has more weight
        if affirmative_count > negative_count:
            return True
        elif negative_count > affirmative_count:
            return False
        
        # Default to False if ambiguous
        logger.warning(f"Ambiguous LLM response for decision: {response[:100]}...")
        return False