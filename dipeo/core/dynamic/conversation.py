"""Conversation dynamic object for managing dialogue history and context."""

from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime

from dipeo.models import Message, ConversationMetadata


class ConversationContext(TypedDict):
    """Context structure returned by conversation.get_context()."""
    messages: List[Message]
    metadata: Optional[ConversationMetadata]
    context: Dict[str, Any]


class Conversation:
    """Manages dialogue history and context.
    
    This dynamic object maintains the state of a conversation including
    all messages exchanged and contextual information that may be needed
    during execution.
    """
    
    def __init__(self):
        """Initialize an empty conversation."""
        self.messages: List[Message] = []
        self.context: Dict[str, Any] = {}
        self.metadata: Optional[ConversationMetadata] = None
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation history.
        
        Args:
            message: The message to add
        """
        # Ensure message has a timestamp if not provided
        if not message.timestamp:
            message.timestamp = datetime.utcnow().isoformat()
        
        self.messages.append(message)
    
    def get_context(self) -> ConversationContext:
        """Get the complete conversation context.
        
        Returns:
            ConversationContext containing messages, metadata, and context
        """
        return ConversationContext(
            messages=self.messages.copy(),
            metadata=self.metadata,
            context=self.context.copy()
        )
    
    def get_latest_message(self) -> Optional[Message]:
        """Get the most recent message in the conversation.
        
        Returns:
            The latest message or None if conversation is empty
        """
        return self.messages[-1] if self.messages else None
    
    def get_messages_by_person(self, person_id: str) -> List[Message]:
        """Get all messages from a specific person.
        
        Args:
            person_id: ID of the person whose messages to retrieve
            
        Returns:
            List of messages from the specified person
        """
        return [msg for msg in self.messages if msg.from_person_id == person_id]
    
    def get_messages_between(self, person1_id: str, person2_id: str) -> List[Message]:
        """Get all messages exchanged between two persons.
        
        Args:
            person1_id: ID of the first person
            person2_id: ID of the second person
            
        Returns:
            List of messages between the two persons
        """
        return [
            msg for msg in self.messages
            if (msg.from_person_id == person1_id and msg.to_person_id == person2_id) or
               (msg.from_person_id == person2_id and msg.to_person_id == person1_id)
        ]
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update the conversation context with new values.
        
        Args:
            updates: Dictionary of context values to merge
        """
        self.context.update(updates)
    
    def set_metadata(self, metadata: ConversationMetadata) -> None:
        """Set the conversation metadata.
        
        Args:
            metadata: Metadata to associate with this conversation
        """
        self.metadata = metadata
    
    def clear(self) -> None:
        """Clear all messages and reset context."""
        self.messages.clear()
        self.context.clear()
        self.metadata = None
    
    def get_token_count(self) -> int:
        """Calculate total token count across all messages.
        
        Returns:
            Sum of token counts from all messages
        """
        return sum(msg.token_count or 0 for msg in self.messages)
    
    def truncate_to_recent(self, max_messages: int) -> List[Message]:
        """Truncate conversation to keep only recent messages.
        
        Args:
            max_messages: Maximum number of messages to keep
            
        Returns:
            List of messages that were removed
        """
        if len(self.messages) <= max_messages:
            return []
        
        removed = self.messages[:-max_messages]
        self.messages = self.messages[-max_messages:]
        return removed
    
    def __repr__(self) -> str:
        """String representation of the Conversation."""
        return (f"Conversation(messages={len(self.messages)}, "
                f"context_keys={list(self.context.keys())}, "
                f"has_metadata={self.metadata is not None})")