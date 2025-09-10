"""Execution orchestrator that coordinates repositories during diagram execution."""

import logging
from typing import TYPE_CHECKING, Any, Optional

from dipeo.diagram_generated import ApiKeyID, Message, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.ports import ConversationRepository, PersonRepository

if TYPE_CHECKING:
    from dipeo.application.execution.use_cases.prompt_loading import PromptLoadingUseCase
    from dipeo.domain.integrations.ports import LLMService as LLMServicePort
    from dipeo.infrastructure.llm.domain_adapters import LLMMemorySelectionAdapter
    from dipeo.infrastructure.llm.domain_adapters.decision import LLMDecisionAdapter

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
        memory_selector: Optional["LLMMemorySelectionAdapter"] = None,
        llm_service: Optional["LLMServicePort"] = None,
    ):
        self._person_repo = person_repository
        self._conversation_repo = conversation_repository
        self._prompt_loading_use_case = prompt_loading_use_case
        self._memory_selector = memory_selector
        self._llm_service = llm_service
        self._execution_logs: dict[str, list[dict[str, Any]]] = {}

        # Unified person cache for all execution-time person management
        self._person_cache: dict[PersonID, Person] = {}

        # LLM Decision adapter for binary decision making
        self._decision_adapter: LLMDecisionAdapter | None = None

        # Wire orchestrator back to repository for brain/hand components
        if hasattr(self._person_repo, "set_orchestrator"):
            self._person_repo.set_orchestrator(self)
        self._current_execution_id: str | None = None

    # ===== Person Management =====

    def get_or_create_person(
        self,
        person_id: PersonID,
        name: str | None = None,
        llm_config: PersonLLMConfig | None = None,
        diagram: Any | None = None,
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

    def get_llm_service(self):
        """Get the LLM service instance."""
        return self._llm_service

    # ===== Conversation Management =====

    def get_conversation(self):
        """Get the global conversation shared by all persons."""
        return self._conversation_repo.get_global_conversation()

    def add_message(self, message: Message, execution_id: str, node_id: str | None = None) -> None:
        """Add a message to the global conversation and log it."""
        self._current_execution_id = execution_id

        # Add to global conversation with metadata
        self._conversation_repo.add_message(message, execution_id, node_id)

        # Log for persistence/debugging (kept for backward compatibility)
        if execution_id not in self._execution_logs:
            self._execution_logs[execution_id] = []

        self._execution_logs[execution_id].append(
            {
                "role": self._get_role_from_message(message),
                "content": message.content,
                "from_person_id": str(message.from_person_id),
                "to_person_id": str(message.to_person_id),
                "node_id": node_id,
                "timestamp": message.timestamp,
            }
        )

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
                log
                for log in self._execution_logs[self._current_execution_id]
                if log.get("from_person_id") != str(person_id)
                and log.get("to_person_id") != str(person_id)
            ]

    # ===== Initialization =====

    async def initialize(self) -> None:
        """Initialize the orchestrator."""
        # Initialize the decision adapter lazily when needed
        # (it requires self, so can't do it in __init__)
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

    def get_person_config(self, person_id: str) -> PersonLLMConfig | None:
        """Get a person's LLM configuration.

        This method exists for backward compatibility.
        """
        person_id_obj = PersonID(person_id)
        if self._person_repo.exists(person_id_obj):
            person = self._person_repo.get(person_id_obj)
            return person.llm_config
        return None

    # ===== LLM Decision Methods =====

    async def make_llm_decision(
        self,
        person_id: PersonID,
        prompt: str,
        template_values: dict[str, Any] | None = None,
        memory_profile: str = "GOLDFISH",
        diagram: Any | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Make a binary decision using LLM.

        This uses the LLMDecisionAdapter internally to handle decision-specific
        logic like decision facets and YES/NO parsing.

        Args:
            person_id: The person to use for decision making
            prompt: The decision prompt
            template_values: Optional template values for the prompt
            memory_profile: Memory profile to use (default: GOLDFISH for unbiased decisions)
            diagram: Optional diagram for person creation from diagram

        Returns:
            Tuple of (decision: bool, metadata: dict with response details)
        """
        # Lazy initialization of decision adapter
        if not self._decision_adapter:
            from dipeo.infrastructure.llm.domain_adapters.decision import LLMDecisionAdapter

            self._decision_adapter = LLMDecisionAdapter(self)

        # Delegate to the adapter
        return await self._decision_adapter.make_decision(
            person_id=person_id,
            prompt=prompt,
            template_values=template_values,
            memory_profile=memory_profile,
            diagram=diagram,
        )

    def load_prompt(
        self,
        prompt_file: str | None = None,
        inline_prompt: str | None = None,
        diagram: Any | None = None,
        node_label: str | None = None,
    ) -> str | None:
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
            node_label=node_label,
        )

    def _create_person_from_diagram(self, person_id: PersonID, diagram: Any) -> Person | None:
        """Create a person from diagram configuration.

        This method is migrated from PersonManagementUseCase to centralize
        person creation logic.

        Args:
            person_id: The person identifier
            diagram: The diagram containing person configurations

        Returns:
            Created Person instance or None if not found in diagram
        """
        # Check if diagram has persons in metadata (ExecutableDiagram)
        persons_catalog = None
        if hasattr(diagram, "metadata") and isinstance(diagram.metadata, dict):
            persons_catalog = diagram.metadata.get("persons", {})
        # Fallback to direct persons attribute (DomainDiagram)
        elif hasattr(diagram, "persons"):
            # Convert persons to catalog format
            persons_catalog = {}
            persons_list = (
                list(diagram.persons.values())
                if isinstance(diagram.persons, dict)
                else diagram.persons
            )
            for person in persons_list:
                p_id = str(person.id) if hasattr(person, "id") else str(person.name)
                person_config_dict = {}
                if hasattr(person, "llm_config"):
                    llm_config = person.llm_config
                    service_value = (
                        llm_config.service if hasattr(llm_config, "service") else "openai"
                    )
                    if hasattr(service_value, "value"):
                        person_config_dict["service"] = service_value.value
                    else:
                        person_config_dict["service"] = str(service_value)
                    person_config_dict["model"] = (
                        str(llm_config.model)
                        if hasattr(llm_config, "model")
                        else "gpt-5-nano-2025-08-07"
                    )
                    person_config_dict["api_key_id"] = (
                        str(llm_config.api_key_id)
                        if hasattr(llm_config, "api_key_id")
                        else "default"
                    )
                    if hasattr(llm_config, "system_prompt") and llm_config.system_prompt:
                        person_config_dict["system_prompt"] = llm_config.system_prompt
                persons_catalog[p_id] = person_config_dict

        if not persons_catalog:
            return None

        # Find person config in catalog
        person_config = None
        for p_id, config in persons_catalog.items():
            if PersonID(p_id) == person_id:
                person_config = config
                break

        if not person_config:
            return None

        # Create LLM config from diagram person config
        # Default to APIKEY_52609F if no api_key_id is specified (common in most diagrams)
        api_key_id = person_config.get("api_key_id")
        if not api_key_id:
            # Try to find a reasonable default from the diagram's other persons
            # or use APIKEY_52609F which is the most common one
            api_key_id = "APIKEY_52609F"
            logger.warning(f"No api_key_id for person {person_id}, defaulting to {api_key_id}")

        # Load system prompt from file if specified
        system_prompt = person_config.get("system_prompt")
        prompt_file = person_config.get("prompt_file")

        if prompt_file and self._prompt_loading_use_case:
            # Load prompt from file using the centralized use case
            loaded_prompt = self.load_prompt(
                prompt_file=prompt_file,
                inline_prompt=None,
                diagram=diagram,
                node_label=f"Person {person_id}",
            )
            if loaded_prompt:
                # Use loaded content as system prompt
                system_prompt = loaded_prompt
                logger.debug(
                    f"Loaded system prompt from file '{prompt_file}' for person {person_id}"
                )

        llm_config = PersonLLMConfig(
            service=person_config.get("service", "openai"),
            model=person_config.get("model", "gpt-5-nano-2025-08-07"),
            api_key_id=ApiKeyID(api_key_id),
            system_prompt=system_prompt,
            prompt_file=None,  # Clear prompt_file since we've already loaded it
        )

        # Create person with config
        person = self._person_repo.get_or_create(
            person_id=person_id,
            name=person_config.get("name", str(person_id)),
            llm_config=llm_config,
        )

        return person

    def register_diagram_persons(self, diagram: Any) -> None:
        """Register all persons defined in a diagram.

        This method ensures all diagram-defined persons are created
        and cached before execution begins.

        Args:
            diagram: The diagram containing person definitions
        """
        # Check if diagram has persons in metadata (ExecutableDiagram)
        persons_catalog = None
        if hasattr(diagram, "metadata") and isinstance(diagram.metadata, dict):
            persons_catalog = diagram.metadata.get("persons", {})
        # Fallback to direct persons attribute (DomainDiagram)
        elif hasattr(diagram, "persons"):
            # Convert persons to catalog format (same logic as _create_person_from_diagram)
            persons_catalog = {}
            persons_list = (
                list(diagram.persons.values())
                if isinstance(diagram.persons, dict)
                else diagram.persons
            )
            for person in persons_list:
                p_id = str(person.id) if hasattr(person, "id") else str(person.name)
                person_config_dict = {}
                if hasattr(person, "llm_config"):
                    llm_config = person.llm_config
                    service_value = (
                        llm_config.service if hasattr(llm_config, "service") else "openai"
                    )
                    if hasattr(service_value, "value"):
                        person_config_dict["service"] = service_value.value
                    else:
                        person_config_dict["service"] = str(service_value)
                    person_config_dict["model"] = (
                        str(llm_config.model)
                        if hasattr(llm_config, "model")
                        else "gpt-5-nano-2025-08-07"
                    )
                    person_config_dict["api_key_id"] = (
                        str(llm_config.api_key_id)
                        if hasattr(llm_config, "api_key_id")
                        else "default"
                    )
                    if hasattr(llm_config, "system_prompt") and llm_config.system_prompt:
                        person_config_dict["system_prompt"] = llm_config.system_prompt
                persons_catalog[p_id] = person_config_dict

        if not persons_catalog:
            return

        for person_id, _config in persons_catalog.items():
            person_id_obj = PersonID(person_id)
            if person_id_obj not in self._person_cache:
                person = self._create_person_from_diagram(person_id_obj, diagram)
                if person:
                    self._person_cache[person_id_obj] = person
                    logger.debug(f"Registered person from diagram: {person_id}")
