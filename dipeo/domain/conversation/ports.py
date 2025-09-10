"""Conversation bounded context ports - defines interfaces for repositories."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Protocol

from dipeo.diagram_generated import LLMService, Message, PersonID, PersonLLMConfig

if TYPE_CHECKING:
    from dipeo.diagram_generated import ChatResult

from . import Conversation, Person


class ConversationRepository(Protocol):
    """Repository protocol for managing Conversation state and operations.

    This combines data persistence with business operations for conversations,
    providing a complete interface for conversation management during execution.
    """

    def get_global_conversation(self) -> Conversation: ...

    def add_message(
        self, message: Message, execution_id: str | None = None, node_id: str | None = None
    ) -> None:
        """Add message to conversations, auto-routing based on from/to fields.

        Args:
            message: The message to add
            execution_id: Optional execution context
            node_id: Optional node context
        """
        ...

    def get_messages(self) -> list[Message]: ...

    def get_conversation_history(self, person_id: PersonID) -> list[dict[str, Any]]:
        """Get conversation history for a specific person.

        Args:
            person_id: The person to get history for

        Returns:
            List of message dictionaries with metadata
        """
        ...

    def clear(self) -> None: ...

    def get_message_count(self) -> int: ...

    def get_latest_message(self) -> Message | None: ...


class PersonRepository(Protocol):
    """Repository protocol for managing Person entities and lifecycle.

    This combines data persistence with business operations for persons,
    providing a complete interface for person management during execution.
    """

    def get(self, person_id: PersonID) -> Person:
        """Retrieve a person by ID.

        Raises:
            KeyError: If person not found
        """
        ...

    def save(self, person: Person) -> None: ...

    def create(
        self,
        person_id: PersonID,
        name: str,
        llm_config: PersonLLMConfig,
    ) -> Person:
        """Create a new person.

        Returns:
            The created Person instance
        """
        ...

    def get_or_create(
        self,
        person_id: PersonID,
        name: str | None = None,
        llm_config: PersonLLMConfig | None = None,
    ) -> Person:
        """Get existing person or create new one with defaults.

        Args:
            person_id: The person identifier
            name: Optional name (defaults to person_id string)
            llm_config: Optional LLM configuration (defaults to gpt-5-nano)

        Returns:
            The retrieved or created Person instance
        """
        ...

    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Register a new person with the given configuration.

        This method exists for backward compatibility with existing code.

        Args:
            person_id: String identifier for the person
            config: Dictionary with 'name', 'service', 'model', 'api_key_id', 'system_prompt'
        """
        ...

    def delete(self, person_id: PersonID) -> None: ...

    def exists(self, person_id: PersonID) -> bool: ...

    def get_all(self) -> dict[PersonID, Person]: ...

    def get_by_service(self, service: LLMService) -> list[Person]: ...

    def clear(self) -> None: ...


class MemorySelectionPort(Protocol):
    """Simplified port for memory selection implementations.

    This simplified interface focuses on the core responsibility of
    selecting relevant message IDs based on criteria.
    """

    async def select_memories(
        self,
        *,
        person_id: PersonID,
        candidate_messages: Sequence[Message],
        task_preview: str,
        criteria: str,
        at_most: int | None = None,
        **kwargs,
    ) -> list[str] | None:
        """Select relevant message IDs based on criteria.

        Args:
            person_id: The person for whom we're selecting memories
            candidate_messages: Pre-filtered and scored messages to select from
            task_preview: Preview of the upcoming task for context
            criteria: Selection criteria (natural language)
            at_most: Maximum number of messages to select
            **kwargs: Additional implementation-specific parameters

        Returns:
            List of selected message IDs, or None if selection not performed
        """
        ...


class MemoryService(Protocol):
    """Service for managing conversation memory and context."""

    async def get_relevant_memory(
        self,
        person_id: PersonID,
        messages: list[Message],
        limit: int = 10,
    ) -> list[Message]: ...

    async def store_interaction(
        self,
        person_id: PersonID,
        messages: list[Message],
        response: "ChatResult",
    ) -> None: ...

    async def clear_memory(self, person_id: PersonID) -> None: ...
