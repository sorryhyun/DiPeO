"""Use case for managing conversations."""

from typing import Optional

from dipeo.diagram_generated import Message
from dipeo.domain.conversation import Conversation, ConversationManager
from dipeo.domain.ports.conversation_repository import ConversationRepository


class ManageConversationUseCase:
    """Use case for managing conversation state and messages.
    
    This use case orchestrates conversation operations including:
    - Adding messages to conversations
    - Retrieving conversation history
    - Clearing conversations
    - Getting conversation statistics
    """
    
    def __init__(
        self, 
        conversation_repository: ConversationRepository,
        conversation_manager: ConversationManager
    ):
        """Initialize the use case with required dependencies.
        
        Args:
            conversation_repository: Repository for persisting conversations
            conversation_manager: Domain service for conversation management
        """
        self.conversation_repository = conversation_repository
        self.conversation_manager = conversation_manager
    
    def add_message(self, message: Message) -> None:
        """Add a message to the global conversation.
        
        Args:
            message: The message to add
        """
        self.conversation_repository.add_message(message)
    
    def get_conversation_history(self) -> list[Message]:
        """Get all messages from the conversation.
        
        Returns:
            List of all messages in chronological order
        """
        return self.conversation_repository.get_messages()
    
    def get_latest_message(self) -> Optional[Message]:
        """Get the most recent message.
        
        Returns:
            The latest message or None if conversation is empty
        """
        return self.conversation_repository.get_latest_message()
    
    def clear_conversation(self) -> None:
        """Clear all messages from the conversation."""
        self.conversation_repository.clear()
    
    def get_conversation_stats(self) -> dict:
        """Get statistics about the conversation.
        
        Returns:
            Dictionary containing conversation statistics
        """
        return {
            "message_count": self.conversation_repository.get_message_count(),
            "has_messages": self.conversation_repository.get_message_count() > 0,
            "latest_message": self.conversation_repository.get_latest_message()
        }
    
    def get_global_conversation(self) -> Conversation:
        """Get the global conversation object.
        
        Returns:
            The global conversation shared by all persons
        """
        return self.conversation_repository.get_global_conversation()