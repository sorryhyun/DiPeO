"""LLM-based decision making adapter."""

import logging
import re
from typing import Any, Optional, TYPE_CHECKING

from dipeo.diagram_generated.domain_models import PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.infrastructure.llm.core.types import ExecutionPhase, DecisionOutput

if TYPE_CHECKING:
    from dipeo.application.execution.orchestrators.execution_orchestrator import ExecutionOrchestrator

logger = logging.getLogger(__name__)


class LLMDecisionAdapter:
    """LLM-based adapter for binary decision making.
    
    This adapter uses an LLM to make binary decisions based on
    natural language prompts and context.
    """
    
    def __init__(self, orchestrator: "ExecutionOrchestrator"):
        """Initialize the LLM decision adapter.
        
        Args:
            orchestrator: The execution orchestrator for LLM operations
        """
        self._orchestrator = orchestrator
        self._facet_cache: dict[str, Person] = {}
    
    def _decision_facet_id(self, person_id: PersonID) -> PersonID:
        """Generate a unique ID for the decision facet.
        
        Args:
            person_id: Base person ID
            
        Returns:
            PersonID for the decision facet
        """
        return PersonID(f"{str(person_id)}.__decision")
    
    def _decision_system_prompt(self, base_prompt: Optional[str]) -> str:
        """Create system prompt for decision making.
        
        Args:
            base_prompt: Optional base system prompt from the person
            
        Returns:
            Complete system prompt for decision making
        """
        base = (base_prompt or "").strip()
        return (
            (base + "\n\n" if base else "")
            + "You are in DECISION MODE.\n"
              "- Evaluate the provided context and make a binary decision.\n"
              "- If the system supports structured output, provide:\n"
              "  - decision: true for YES/affirmative/valid/approved\n"
              "  - decision: false for NO/negative/invalid/rejected\n"
              "  - reasoning: brief explanation (optional)\n"
              "- Otherwise, respond with YES or NO at the start, followed by optional explanation.\n"
              "- Be decisive and clear in your judgment."
        )
    
    def _get_or_create_decision_facet(self, person_id: PersonID, diagram: Optional[Any] = None) -> Person:
        """Get or create a decision facet for the person.
        
        Args:
            person_id: The person ID to create a facet for
            diagram: Optional diagram for person creation from diagram
            
        Returns:
            Person instance configured for decision making
        """
        facet_id = self._decision_facet_id(person_id)
        persons = self._orchestrator.get_all_persons()
        if facet_id in persons:
            return persons[facet_id]
        
        # Get the base person to derive LLM config (create if doesn't exist)
        base_person = self._orchestrator.get_or_create_person(person_id, diagram=diagram)
        llm = base_person.llm_config
        
        facet_cfg = PersonLLMConfig(
            service=llm.service,
            model=llm.model,
            api_key_id=llm.api_key_id,
            system_prompt=self._decision_system_prompt(llm.system_prompt),
            prompt_file=None,
        )
        
        facet = self._orchestrator.get_or_create_person(
            person_id=facet_id,
            name=f"{base_person.name} (Decision)",
            llm_config=facet_cfg
        )
        
        self._facet_cache[str(facet_id)] = facet
        return facet
    
    async def make_decision(
        self,
        person_id: PersonID,
        prompt: str,
        template_values: Optional[dict[str, Any]] = None,
        memory_profile: str = "GOLDFISH",
        diagram: Optional[Any] = None
    ) -> tuple[bool, dict[str, Any]]:
        """Make a binary decision using LLM.
        
        Args:
            person_id: The person to use for decision making
            prompt: The decision prompt
            template_values: Optional template values for the prompt
            memory_profile: Memory profile to use (default: GOLDFISH for unbiased decisions)
            diagram: Optional diagram for person creation from diagram
            
        Returns:
            Tuple of (decision: bool, metadata: dict with response details)
        """
        if not prompt or not prompt.strip():
            logger.error("Empty prompt provided for decision")
            return False, {"error": "Empty prompt"}
        
        # Get or create decision facet
        facet = self._get_or_create_decision_facet(person_id, diagram=diagram)
        
        # Get LLM service from orchestrator
        llm_service = self._orchestrator.get_llm_service()
        if not llm_service:
            logger.error("LLM service not available from orchestrator")
            return False, {"error": "LLM service not available"}
        
        # Execute decision using person's complete method
        complete_kwargs = {
            "prompt": prompt,
            "all_messages": [],  # Empty for fresh decision
            "llm_service": llm_service,  # Pass the LLM service
            "temperature": 0,  # Deterministic decisions
            "max_tokens": 500,  # Decisions should be concise
            "execution_phase": ExecutionPhase.DECISION_EVALUATION,
        }
        
        try:
            result, incoming_msg, response_msg = await facet.complete(**complete_kwargs)
            
            # Add messages to conversation if orchestrator supports it
            if hasattr(self._orchestrator, 'add_message'):
                self._orchestrator.add_message(incoming_msg, "decision", "decision_maker")
                self._orchestrator.add_message(response_msg, "decision", "decision_maker")
            
            # Check for structured output first
            if hasattr(result, 'structured_output') and result.structured_output:
                # Use structured output if available (from providers that support it)
                if isinstance(result.structured_output, DecisionOutput):
                    decision = result.structured_output.decision
                    reasoning = result.structured_output.reasoning
                    logger.debug(f"LLM Decision - Using structured output: {decision}")
                else:
                    # Fallback to text parsing
                    response_text = getattr(result, "text", "") or ""
                    decision = self._parse_decision(response_text)
                    reasoning = None
            else:
                # Parse from text response
                response_text = getattr(result, "text", "") or ""
                decision = self._parse_decision(response_text)
                reasoning = None
            
            response_text = getattr(result, "text", "") or ""
            logger.debug(f"LLM Decision - Prompt: {prompt[:100]}...")
            logger.debug(f"LLM Decision - Response: {response_text[:200]}")
            logger.debug(f"LLM Decision - Parsed as: {decision}")
            
            metadata = {
                "response": response_text,
                "response_preview": response_text[:200],
                "decision": decision,
                "person": str(person_id),
                "memory_profile": memory_profile
            }
            
            if reasoning:
                metadata["reasoning"] = reasoning
            
            return decision, metadata
            
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return False, {"error": str(e)}
    
    def _parse_decision(self, response: str) -> bool:
        """Parse LLM response to extract boolean decision.
        
        Looks for affirmative/negative keywords to determine decision.
        
        Args:
            response: The LLM response text
            
        Returns:
            Boolean decision
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