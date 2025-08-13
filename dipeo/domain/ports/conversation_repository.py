"""Conversation repository protocol - defines interface for conversation persistence."""

from typing import Protocol

from dipeo.diagram_generated import Message

from ..conversation import Conversation


class ConversationRepository(Protocol):
    """Repository protocol for managing Conversation state.
    
    This defines the interface for persisting and retrieving
    the global conversation during execution.
    """
    
    def get_global_conversation(self) -> Conversation:
        """Get the global conversation shared by all persons."""
        ...
    
    def add_message(self, message: Message) -> None:
        """Add a message to the global conversation."""
        ...
    
    def get_messages(self) -> list[Message]:
        """Get all messages from the global conversation."""
        ...
    
    def clear(self) -> None:
        """Clear all messages from the conversation."""
        ...
    
    def get_message_count(self) -> int:
        """Get the number of messages in the conversation."""
        ...
    
    def get_latest_message(self) -> Message | None:
        """Get the most recent message, if any."""
        ...