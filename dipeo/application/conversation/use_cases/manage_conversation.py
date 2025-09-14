"""Use case for managing conversations."""

from typing import Any

from dipeo.diagram_generated import Message, PersonID
from dipeo.domain.conversation import Conversation
from dipeo.domain.conversation.ports import ConversationRepository


class ManageConversationUseCase:
    """Orchestrates conversation operations and message management."""

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    def add_message(self, message: Message) -> None:
        self.conversation_repository.add_message(message)

    def add_message_with_context(
        self, message: Message, execution_id: str, node_id: str | None = None
    ) -> None:
        self.conversation_repository.add_message(message, execution_id, node_id)

    def get_conversation_history(self) -> list[Message]:
        return self.conversation_repository.get_messages()

    def get_person_conversation_history(self, person_id: PersonID | str) -> list[dict[str, Any]]:
        """Get conversation history formatted for person's perspective."""
        person_id_obj = PersonID(person_id) if isinstance(person_id, str) else person_id
        return self.conversation_repository.get_conversation_history(person_id_obj)

    def get_latest_message(self) -> Message | None:
        return self.conversation_repository.get_latest_message()

    def clear_conversation(self) -> None:
        self.conversation_repository.clear()

    def get_conversation_stats(self) -> dict:
        return {
            "message_count": self.conversation_repository.get_message_count(),
            "has_messages": self.conversation_repository.get_message_count() > 0,
            "latest_message": self.conversation_repository.get_latest_message(),
        }

    def get_global_conversation(self) -> Conversation:
        """Get the global conversation shared by all persons."""
        return self.conversation_repository.get_global_conversation()
