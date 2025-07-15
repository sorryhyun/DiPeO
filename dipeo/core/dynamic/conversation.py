"""Conversation dynamic object for managing dialogue history and context."""

from datetime import datetime
from typing import Any, TypedDict

from dipeo.models import ConversationMetadata, Message


class ConversationContext(TypedDict):
    """Context structure returned by conversation.get_context()."""
    messages: list[Message]
    metadata: ConversationMetadata | None
    context: dict[str, Any]


class Conversation:
    """Manages dialogue history and context.
    
    Maintains conversation state including messages and execution context.
    """
    
    def __init__(self):
        self.messages: list[Message] = []
        self.context: dict[str, Any] = {}
        self.metadata: ConversationMetadata | None = None
    
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
    
    def get_latest_message(self) -> Message | None:
        # Get most recent message
        return self.messages[-1] if self.messages else None
    
    
    def update_context(self, updates: dict[str, Any]) -> None:
        # Update context with new values
        self.context.update(updates)
    
    
    def clear(self) -> None:
        self.messages.clear()
        self.context.clear()
        self.metadata = None
    
    
    def __repr__(self) -> str:
        return (f"Conversation(messages={len(self.messages)}, "
                f"context_keys={list(self.context.keys())}, "
                f"has_metadata={self.metadata is not None})")