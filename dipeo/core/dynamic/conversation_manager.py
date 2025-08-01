"""Protocol for managing conversation flow and memory during execution."""

from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable

from dipeo.models import Message

from .conversation import Conversation


@runtime_checkable
class ConversationManager(Protocol):
    
    @abstractmethod
    def get_conversation(self, person_id: str = "") -> Conversation:
        """Get global conversation. person_id parameter ignored for backward compatibility."""
        ...
    
    
    @abstractmethod
    def add_message(
        self,
        message: Message,
        execution_id: str,
        node_id: str | None = None
    ) -> None:
        """Add message to conversations, auto-routing based on from/to fields."""
        ...
    
    @abstractmethod
    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        ...
    
    @abstractmethod
    def clear_all_conversations(self) -> None:
        ...
    


