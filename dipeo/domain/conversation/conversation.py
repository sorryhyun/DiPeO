"""Conversation dynamic object for managing dialogue history and context."""

from datetime import datetime
from typing import Any, TypedDict
from uuid import uuid4

from dipeo.diagram_generated import ConversationMetadata, Message


class ConversationContext(TypedDict):
    messages: list[Message]
    metadata: ConversationMetadata | None
    context: dict[str, Any]


class Conversation:
    def __init__(self):
        self.messages: list[Message] = []
        self.context: dict[str, Any] = {}
        self.metadata: ConversationMetadata | None = None

    def add_message(self, message: Message) -> None:
        if not message.timestamp:
            message.timestamp = datetime.utcnow().isoformat()

        # Generate ID if not present
        if not message.id:
            message.id = str(uuid4())[:6]

        self.messages.append(message)

    def get_context(self) -> ConversationContext:
        return ConversationContext(
            messages=self.messages.copy(), metadata=self.metadata, context=self.context.copy()
        )

    def get_latest_message(self) -> Message | None:
        return self.messages[-1] if self.messages else None

    def update_context(self, updates: dict[str, Any]) -> None:
        self.context.update(updates)

    def clear(self) -> None:
        self.messages.clear()
        self.context.clear()
        self.metadata = None

    def __repr__(self) -> str:
        return (
            f"Conversation(messages={len(self.messages)}, "
            f"context_keys={list(self.context.keys())}, "
            f"has_metadata={self.metadata is not None})"
        )
