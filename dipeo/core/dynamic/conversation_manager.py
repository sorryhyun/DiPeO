"""Protocol for managing conversation flow and memory during execution."""

from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable

from dipeo.models import Message

from .conversation import Conversation


@runtime_checkable
class ConversationManager(Protocol):
    """Manages conversation state and memory during diagram execution."""
    
    @abstractmethod
    def get_conversation(self, person_id: str = "") -> Conversation:
        """Get the global conversation.
        
        Args:
            person_id: Deprecated parameter for backward compatibility (ignored)
            
        Returns:
            Global Conversation object with messages, context, and metadata
        """
        ...
    
    
    @abstractmethod
    def add_message(
        self,
        message: Message,
        execution_id: str,
        node_id: str | None = None
    ) -> None:
        """Add a message to relevant conversations based on from/to fields.
        
        Messages are automatically routed to appropriate conversations:
        - Added to sender's conversation (if from_person_id != "system")
        - Added to recipient's conversation (if to_person_id != "system")
        
        Args:
            message: The message to add (contains from_person_id and to_person_id)
            execution_id: The current execution ID
            node_id: Optional ID of the node that generated this message
        """
        ...
    
    @abstractmethod
    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        """Get conversation history as a list of message dictionaries.
        
        Args:
            person_id: The ID of the person
            
        Returns:
            List of message dictionaries with role and content
        """
        ...
    
    @abstractmethod
    def clear_all_conversations(self) -> None:
        """Clear all conversations."""
        ...
    


