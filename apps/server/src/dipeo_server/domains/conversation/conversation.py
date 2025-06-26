from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """Enhanced message with metadata."""

    id: str
    role: str
    content: str
    timestamp: datetime
    sender_person_id: Optional[str] = None
    execution_id: Optional[str] = None
    node_id: Optional[str] = None
    node_label: Optional[str] = None
    token_count: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
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
    """Conversation state for a specific person with proper cleanup."""

    person_id: str
    messages: List[Message] = field(default_factory=list)
    forgotten_message_ids: set[str] = field(default_factory=set)
    last_execution_id: Optional[str] = None
    MAX_MESSAGES = 100

    def add_message(self, message: Message) -> None:
        """Add a message to conversation with automatic cleanup of old messages."""
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
        """Mark all messages sent BY this person as forgotten."""
        for message in self.messages:
            if message.sender_person_id == self.person_id:
                self.forgotten_message_ids.add(message.id)

    def forget_own_messages_from_execution(self, execution_id: str) -> None:
        """Mark messages sent BY this person from a specific execution as forgotten."""
        for message in self.messages:
            if (
                message.execution_id == execution_id
                and message.sender_person_id == self.person_id
            ):
                self.forgotten_message_ids.add(message.id)

    def get_visible_messages(self, current_person_id: str) -> List[Dict[str, Any]]:
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


