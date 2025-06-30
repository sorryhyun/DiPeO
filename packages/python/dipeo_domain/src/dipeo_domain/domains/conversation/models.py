"""Extended conversation models that build on generated base models."""

from dataclasses import dataclass, field
from typing import Any

from dipeo_domain.models import Message as BaseMessage


@dataclass
class PersonConversation:
    """Simplified conversation state for a person."""

    person_id: str
    messages: list[BaseMessage] = field(default_factory=list)

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
