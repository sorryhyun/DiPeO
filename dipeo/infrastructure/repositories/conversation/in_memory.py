"""In-memory implementation of ConversationRepository."""

from typing import Any

from dipeo.diagram_generated import Message, PersonID
from dipeo.domain.conversation import Conversation
from dipeo.domain.conversation.ports import ConversationRepository


class InMemoryConversationRepository(ConversationRepository):
    """In-memory ConversationRepository with global conversation."""

    def __init__(self):
        self._global_conversation = Conversation()

    def get_global_conversation(self) -> Conversation:
        return self._global_conversation

    def add_message(
        self, message: Message, execution_id: str | None = None, node_id: str | None = None
    ) -> None:
        if execution_id or node_id:
            if not message.metadata:
                message.metadata = {}
            if execution_id:
                message.metadata["execution_id"] = execution_id
            if node_id:
                message.metadata["node_id"] = node_id

        self._global_conversation.add_message(message)

    def get_messages(self) -> list[Message]:
        return self._global_conversation.messages.copy()

    def get_conversation_history(self, person_id: PersonID) -> list[dict[str, Any]]:
        """Get conversation history formatted for the person's perspective."""
        history = []
        for msg in self._global_conversation.messages:
            if msg.from_person_id == person_id or msg.to_person_id == person_id:
                role = "assistant" if msg.from_person_id == person_id else "user"
                if msg.from_person_id == "system":
                    role = "system"

                history.append(
                    {
                        "role": role,
                        "content": msg.content,
                        "from_person_id": str(msg.from_person_id),
                        "to_person_id": str(msg.to_person_id),
                        "timestamp": msg.timestamp,
                        "metadata": msg.metadata,
                    }
                )

        return history

    def clear(self) -> None:
        self._global_conversation.clear()

    def get_message_count(self) -> int:
        return len(self._global_conversation.messages)

    def get_latest_message(self) -> Message | None:
        return self._global_conversation.get_latest_message()
