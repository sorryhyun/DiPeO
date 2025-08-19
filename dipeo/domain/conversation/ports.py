"""Conversation bounded context ports - defines interfaces for repositories."""

from typing import Any, Optional, Protocol

from dipeo.diagram_generated import LLMService, Message, PersonID, PersonLLMConfig

from . import Conversation, Person


class ConversationRepository(Protocol):
    """Repository protocol for managing Conversation state and operations.
    
    This combines data persistence with business operations for conversations,
    providing a complete interface for conversation management during execution.
    """
    
    def get_global_conversation(self) -> Conversation:
        """Get the global conversation shared by all persons."""
        ...
    
    def add_message(
        self,
        message: Message,
        execution_id: str | None = None,
        node_id: str | None = None
    ) -> None:
        """Add message to conversations, auto-routing based on from/to fields.
        
        Args:
            message: The message to add
            execution_id: Optional execution context
            node_id: Optional node context
        """
        ...
    
    def get_messages(self) -> list[Message]:
        """Get all messages from the global conversation."""
        ...
    
    def get_conversation_history(self, person_id: PersonID) -> list[dict[str, Any]]:
        """Get conversation history for a specific person.
        
        Args:
            person_id: The person to get history for
            
        Returns:
            List of message dictionaries with metadata
        """
        ...
    
    def clear(self) -> None:
        """Clear all messages from the conversation."""
        ...
    
    def clear_person_messages(self, person_id: PersonID) -> None:
        """Clear all messages involving a specific person.
        
        Args:
            person_id: The person whose messages to clear
        """
        ...
    
    def get_message_count(self) -> int:
        """Get the number of messages in the conversation."""
        ...
    
    def get_latest_message(self) -> Message | None:
        """Get the most recent message, if any."""
        ...


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
    
    def save(self, person: Person) -> None:
        """Save or update a person."""
        ...
    
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
        name: Optional[str] = None,
        llm_config: Optional[PersonLLMConfig] = None
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
    
    def delete(self, person_id: PersonID) -> None:
        """Delete a person by ID."""
        ...
    
    def exists(self, person_id: PersonID) -> bool:
        """Check if a person exists."""
        ...
    
    def get_all(self) -> dict[PersonID, Person]:
        """Get all persons."""
        ...
    
    def get_by_service(self, service: LLMService) -> list[Person]:
        """Get all persons using a specific LLM service."""
        ...
    
    def clear(self) -> None:
        """Clear all persons."""
        ...