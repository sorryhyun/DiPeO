"""Execution orchestrator that coordinates repositories during diagram execution."""

import logging
from typing import Any, Optional, TYPE_CHECKING

from dipeo.diagram_generated import ApiKeyID, LLMService, Message, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Conversation, Person
from dipeo.domain.conversation.ports import ConversationRepository, PersonRepository
from dipeo.infrastructure.llm.core.types import ExecutionPhase, LLMResponse

if TYPE_CHECKING:
    from dipeo.application.execution.use_cases.prompt_loading import PromptLoadingUseCase
    from dipeo.infrastructure.memory.llm_memory_selector import LLMMemorySelector
    from dipeo.domain.integrations.ports import LLMService as LLMServicePort

logger = logging.getLogger(__name__)


class ExecutionOrchestrator:
    """Orchestrates person and conversation management during execution.
    
    This service coordinates between PersonRepository and ConversationRepository,
    ensuring proper wiring and interaction between persons and conversations.
    It also provides centralized person caching, prompt loading, and LLM decision execution.
    """
    
    def __init__(
        self,
        person_repository: PersonRepository,
        conversation_repository: ConversationRepository,
        prompt_loading_use_case: Optional["PromptLoadingUseCase"] = None,
        memory_selector: Optional["LLMMemorySelector"] = None,
        llm_service: Optional["LLMServicePort"] = None
    ):
        self._person_repo = person_repository
        self._conversation_repo = conversation_repository
        self._prompt_loading_use_case = prompt_loading_use_case
        self._memory_selector = memory_selector
        self._llm_service = llm_service
        self._execution_logs: dict[str, list[dict[str, Any]]] = {}
        
        # Unified person cache for all execution-time person management
        self._person_cache: dict[PersonID, Person] = {}
        
        # Wire orchestrator back to repository for brain/hand components
        if hasattr(self._person_repo, 'set_orchestrator'):
            self._person_repo.set_orchestrator(self)
        self._current_execution_id: Optional[str] = None
    
    # ===== Person Management =====
    
    def get_or_create_person(
        self,
        person_id: PersonID,
        name: Optional[str] = None,
        llm_config: Optional[PersonLLMConfig] = None,
        diagram: Optional[Any] = None
    ) -> Person:
        """Get existing person or create new one with centralized caching.
        
        Args:
            person_id: The person identifier
            name: Optional name for the person
            llm_config: Optional LLM configuration
            diagram: Optional diagram for person creation from diagram
            
        Returns:
            The Person instance (cached)
        """
        # Check cache first
        if person_id in self._person_cache:
            return self._person_cache[person_id]
        
        # If diagram is provided and person not in cache, try to create from diagram
        if diagram and not self._person_repo.exists(person_id):
            person = self._create_person_from_diagram(person_id, diagram)
            if person:
                self._person_cache[person_id] = person
                return person
        
        # Otherwise use repository's get_or_create
        person = self._person_repo.get_or_create(person_id, name, llm_config)
        self._person_cache[person_id] = person
        return person
    
    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Register a new person with the given configuration.
        
        This method exists for backward compatibility with existing code.
        """
        self._person_repo.register_person(person_id, config)
    
    def get_person(self, person_id: PersonID) -> Person:
        """Get a person by ID."""
        return self._person_repo.get(person_id)
    
    def get_all_persons(self) -> dict[PersonID, Person]:
        """Get all registered persons."""
        return self._person_repo.get_all()
    
    # ===== Conversation Management =====
    
    def get_conversation(self):
        """Get the global conversation shared by all persons."""
        return self._conversation_repo.get_global_conversation()
    
    def add_message(
        self,
        message: Message,
        execution_id: str,
        node_id: Optional[str] = None
    ) -> None:
        """Add a message to the global conversation and log it."""
        self._current_execution_id = execution_id
        
        # Add to global conversation with metadata
        self._conversation_repo.add_message(message, execution_id, node_id)
        
        # Log for persistence/debugging (kept for backward compatibility)
        if execution_id not in self._execution_logs:
            self._execution_logs[execution_id] = []
        
        self._execution_logs[execution_id].append({
            "role": self._get_role_from_message(message),
            "content": message.content,
            "from_person_id": str(message.from_person_id),
            "to_person_id": str(message.to_person_id),
            "node_id": node_id,
            "timestamp": message.timestamp
        })
    
    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        """Get conversation history from a person's perspective.
        
        This uses the person's memory filters to provide their view
        of the conversation.
        """
        person_id_obj = PersonID(person_id)
        
        if not self._person_repo.exists(person_id_obj):
            return []
        
        # Use repository's conversation history method
        history = self._conversation_repo.get_conversation_history(person_id_obj)
        
        # Add execution context if available
        if self._current_execution_id:
            for entry in history:
                entry["execution_id"] = self._current_execution_id
        
        return history
    
    def clear_all_conversations(self) -> None:
        """Clear all conversations and reset person memories."""
        # Clear global conversation
        self._conversation_repo.clear()
        
        # Reset each person's memory configuration
        for _person_id, person in self._person_repo.get_all().items():
            person.set_memory_limit(-1)  # Remove limit
            person.set_memory_view(person.memory_view)  # Reset to default view
        
        # Clear execution logs
        self._execution_logs.clear()
        self._current_execution_id = None
    
    def clear_person_messages(self, person_id: PersonID) -> None:
        """Clear all messages involving a specific person from the conversation.
        
        This is used for GOLDFISH memory profile to ensure complete memory reset
        between diagram executions.
        """
        # Delegate to repository
        self._conversation_repo.clear_person_messages(person_id)
        
        # Also clear from execution logs (kept for backward compatibility)
        if self._current_execution_id and self._current_execution_id in self._execution_logs:
            self._execution_logs[self._current_execution_id] = [
                log for log in self._execution_logs[self._current_execution_id]
                if log.get("from_person_id") != str(person_id) and log.get("to_person_id") != str(person_id)
            ]
    
    # ===== Initialization =====
    
    async def initialize(self) -> None:
        """Initialize the orchestrator."""
        # No need to wire up persons anymore
        pass
    
    # ===== Helper Methods =====
    
    @staticmethod
    def _get_role_from_message(message: Message) -> str:
        """Determine the role of a message for logging."""
        if message.from_person_id == "system":
            return "system"
        elif message.from_person_id == message.to_person_id:
            return "assistant"
        else:
            return "user"
    
    def get_person_config(self, person_id: str) -> Optional[PersonLLMConfig]:
        """Get a person's LLM configuration.
        
        This method exists for backward compatibility.
        """
        person_id_obj = PersonID(person_id)
        if self._person_repo.exists(person_id_obj):
            person = self._person_repo.get(person_id_obj)
            return person.llm_config
        return None
    
    # ===== New Centralized Methods =====
    
    async def execute_llm_decision(
        self,
        person_id: str,
        prompt_content: str,
        template_values: dict[str, Any],
        memory_profile: str = "GOLDFISH",
        execution_phase: ExecutionPhase = ExecutionPhase.DECISION_EVALUATION,
        at_most: Optional[int] = None
    ) -> LLMResponse:
        """Execute LLM call with proper person, memory, and prompt handling.
        
        This centralizes the logic for LLM-based decisions, managing:
        - Person creation/retrieval (with caching)
        - Memory selection based on profile
        - Template processing
        - LLM execution
        
        Args:
            person_id: ID of the person to use for the decision
            prompt_content: The prompt content (already loaded)
            template_values: Values for template substitution
            memory_profile: Memory management strategy
            execution_phase: The phase of execution (for phase-aware adapters)
            at_most: Maximum messages for CUSTOM memory profile
            
        Returns:
            LLMResponse from the LLM service
        """
        if not self._llm_service:
            raise ValueError("LLM service not configured for orchestrator")
        
        # Get or create person with caching
        person_id_obj = PersonID(person_id)
        person = self.get_or_create_person(person_id_obj)
        
        # Get conversation history based on memory profile
        messages = []
        if memory_profile != "GOLDFISH":
            # Get conversation history from person's perspective
            history = self.get_conversation_history(person_id)
            
            # Apply memory profile filtering
            if memory_profile == "MINIMAL":
                # System + last 5 messages
                system_msgs = [m for m in history if m.get("role") == "system"]
                non_system = [m for m in history if m.get("role") != "system"]
                messages = system_msgs + non_system[-5:]
            elif memory_profile == "FOCUSED":
                # Last 20 conversation pairs
                messages = history[-40:]  # 20 pairs = 40 messages
            elif memory_profile == "FULL":
                messages = history
            elif memory_profile == "CUSTOM" and at_most:
                # Custom with at_most limit
                messages = history[-at_most:]
        
        # Execute LLM call
        response = await self._llm_service.complete(
            messages=messages,
            prompt=prompt_content,
            model=person.llm_config.model if person.llm_config else None,
            service=person.llm_config.service if person.llm_config else None,
            api_key_id=person.llm_config.api_key_id if person.llm_config else None,
            temperature=0,  # Decision evaluation should be deterministic
            execution_phase=execution_phase.value if execution_phase else None
        )
        
        return response
    
    def load_prompt(
        self,
        prompt_file: Optional[str] = None,
        inline_prompt: Optional[str] = None,
        diagram: Optional[Any] = None,
        node_label: Optional[str] = None
    ) -> Optional[str]:
        """Load prompt content using the centralized PromptLoadingUseCase.
        
        Args:
            prompt_file: Path to external prompt file
            inline_prompt: Inline prompt content
            diagram: Optional diagram for path resolution
            node_label: Optional node label for logging
            
        Returns:
            Prompt content as string, or None if not found
        """
        if not self._prompt_loading_use_case:
            # Fallback to inline prompt if no use case configured
            logger.warning("PromptLoadingUseCase not configured, using inline prompt only")
            return inline_prompt
        
        # Get diagram source path if available
        diagram_source_path = None
        if diagram:
            diagram_source_path = self._prompt_loading_use_case.get_diagram_source_path(diagram)
        
        return self._prompt_loading_use_case.load_prompt(
            prompt_file=prompt_file,
            inline_prompt=inline_prompt,
            diagram_source_path=diagram_source_path,
            node_label=node_label
        )
    
    def _create_person_from_diagram(self, person_id: PersonID, diagram: Any) -> Optional[Person]:
        """Create a person from diagram configuration.
        
        This method is migrated from PersonManagementUseCase to centralize
        person creation logic.
        
        Args:
            person_id: The person identifier
            diagram: The diagram containing person configurations
            
        Returns:
            Created Person instance or None if not found in diagram
        """
        if not diagram or not hasattr(diagram, 'persons'):
            return None
        
        # Find person config in diagram
        person_config = None
        for p_id, config in diagram.persons.items():
            if PersonID(p_id) == person_id:
                person_config = config
                break
        
        if not person_config:
            return None
        
        # Create LLM config from diagram person config
        llm_config = PersonLLMConfig(
            service=person_config.get('service', 'openai'),
            model=person_config.get('model', 'gpt-5-nano-2025-08-07'),
            api_key_id=person_config.get('api_key_id'),
            system_prompt=person_config.get('system_prompt'),
            prompt_file=person_config.get('prompt_file')
        )
        
        # Create person with config
        person = self._person_repo.get_or_create(
            person_id=person_id,
            name=person_config.get('name', str(person_id)),
            llm_config=llm_config
        )
        
        return person
    
    def register_diagram_persons(self, diagram: Any) -> None:
        """Register all persons defined in a diagram.
        
        This method ensures all diagram-defined persons are created
        and cached before execution begins.
        
        Args:
            diagram: The diagram containing person definitions
        """
        if not diagram or not hasattr(diagram, 'persons'):
            return
        
        for person_id, config in diagram.persons.items():
            person_id_obj = PersonID(person_id)
            if person_id_obj not in self._person_cache:
                person = self._create_person_from_diagram(person_id_obj, diagram)
                if person:
                    self._person_cache[person_id_obj] = person
                    logger.debug(f"Registered person from diagram: {person_id}")
