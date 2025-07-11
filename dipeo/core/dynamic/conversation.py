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
    
    Maintains conversation state including messages and execution context.
    """
    
    def __init__(self):
        self.messages: List[Message] = []
        self.context: Dict[str, Any] = {}
        self.metadata: Optional[ConversationMetadata] = None
    
    def add_message(self, message: Message) -> None:
        # Add message with timestamp if missing
        # Ensure message has a timestamp if not provided
        if not message.timestamp:
            message.timestamp = datetime.utcnow().isoformat()
        
        self.messages.append(message)
    
    def get_context(self) -> ConversationContext:
        # Get complete conversation context
        return ConversationContext(
            messages=self.messages.copy(),
            metadata=self.metadata,
            context=self.context.copy()
        )
    
    def get_latest_message(self) -> Optional[Message]:
        # Get most recent message
        return self.messages[-1] if self.messages else None
    
    def get_messages_by_person(self, person_id: str) -> List[Message]:
        # Get messages from specific person
        return [msg for msg in self.messages if msg.from_person_id == person_id]
    
    def get_messages_between(self, person1_id: str, person2_id: str) -> List[Message]:
        # Get messages between two persons
        return [
            msg for msg in self.messages
            if (msg.from_person_id == person1_id and msg.to_person_id == person2_id) or
               (msg.from_person_id == person2_id and msg.to_person_id == person1_id)
        ]
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        # Update context with new values
        self.context.update(updates)
    
    def set_metadata(self, metadata: ConversationMetadata) -> None:
        # Set conversation metadata
        self.metadata = metadata
    
    def clear(self) -> None:
        self.messages.clear()
        self.context.clear()
        self.metadata = None
    
    def get_token_count(self) -> int:
        # Calculate total token count
        return sum(msg.token_count or 0 for msg in self.messages)
    
    def truncate_to_recent(self, max_messages: int) -> List[Message]:
        # Truncate to keep only recent messages
        if len(self.messages) <= max_messages:
            return []
        
        removed = self.messages[:-max_messages]
        self.messages = self.messages[-max_messages:]
        return removed
    
    def __repr__(self) -> str:
        return (f"Conversation(messages={len(self.messages)}, "
                f"context_keys={list(self.context.keys())}, "
                f"has_metadata={self.metadata is not None})")