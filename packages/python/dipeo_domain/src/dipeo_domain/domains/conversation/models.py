"""Extended conversation models that build on generated base models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from dipeo_domain.models import Message as BaseMessage


@dataclass
class ExecutionMessage:
    """Enhanced message with execution context.

    This extends the base Message model with additional fields needed for
    execution tracking and conversation management.
    """

    # Core fields from base Message
    id: str
    person_id: str
    role: str
    content: str
    timestamp: datetime

    # Extended fields for execution context
    sender_person_id: Optional[str] = None
    execution_id: Optional[str] = None
    node_id: Optional[str] = None
    node_label: Optional[str] = None

    # Extended token tracking
    token_count: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None

    @classmethod
    def from_base_message(cls, base_msg: BaseMessage, **kwargs) -> "ExecutionMessage":
        """Create ExecutionMessage from base Message model."""
        # Convert string timestamp to datetime if needed
        timestamp = base_msg.timestamp
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        else:
            timestamp = timestamp

        return cls(
            id=base_msg.id or kwargs.get("id", ""),
            person_id=str(base_msg.person_id),
            role=base_msg.role,
            content=base_msg.content,
            timestamp=timestamp,
            token_count=int(base_msg.token_count) if base_msg.token_count else None,
            **kwargs,
        )

    def to_base_message(self) -> BaseMessage:
        """Convert to base Message model."""
        return BaseMessage(
            id=self.id,
            personId=self.person_id,  # Use alias
            role=self.role,  # type: ignore
            content=self.content,
            timestamp=self.timestamp.isoformat(),
            tokenCount=float(self.token_count) if self.token_count else None,
            metadata={
                "sender_person_id": self.sender_person_id,
                "execution_id": self.execution_id,
                "node_id": self.node_id,
                "node_label": self.node_label,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cached_tokens": self.cached_tokens,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "sender_person_id": self.sender_person_id,
            "execution_id": self.execution_id,
            "node_id": self.node_id,
            "node_label": self.node_label,
            "token_count": self.token_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
        }


@dataclass
class PersonConversation:
    """Conversation state for a specific person with proper cleanup.

    This model is not generated from TypeScript as it's specific to the
    server-side conversation management implementation.
    """

    person_id: str
    messages: list[ExecutionMessage] = field(default_factory=list)
    forgotten_message_ids: set[str] = field(default_factory=set)
    last_execution_id: Optional[str] = None
    MAX_MESSAGES = 100

    def add_message(self, message: ExecutionMessage) -> None:
        """Add a message and enforce message limit."""
        self.messages.append(message)

        if len(self.messages) > self.MAX_MESSAGES:
            messages_to_remove = len(self.messages) - self.MAX_MESSAGES
            self.messages = self.messages[messages_to_remove:]

            remaining_ids = {msg.id for msg in self.messages}
            self.forgotten_message_ids &= remaining_ids

    def forget_messages_from_execution(self, execution_id: str) -> None:
        """Mark messages from a specific execution as forgotten."""
        for message in self.messages:
            if message.execution_id == execution_id:
                self.forgotten_message_ids.add(message.id)

    def forget_own_messages(self) -> None:
        """Mark all messages from this person as forgotten."""
        for message in self.messages:
            if message.sender_person_id == self.person_id:
                self.forgotten_message_ids.add(message.id)

    def forget_own_messages_from_execution(self, execution_id: str) -> None:
        """Mark own messages from a specific execution as forgotten."""
        for message in self.messages:
            if (
                message.execution_id == execution_id
                and message.sender_person_id == self.person_id
            ):
                self.forgotten_message_ids.add(message.id)

    def get_visible_messages(self, current_person_id: str) -> list[dict[str, Any]]:
        """Get messages visible to a specific person."""
        visible_messages = []

        for message in self.messages:
            if message.id in self.forgotten_message_ids:
                continue

            role = (
                "assistant" if message.sender_person_id == current_person_id else "user"
            )

            if role == "user" and message.node_label:
                content = f"[{message.node_label}]: {message.content}"
            else:
                content = message.content

            visible_messages.append(
                {"role": role, "content": content, "personId": message.sender_person_id}
            )

        return visible_messages
