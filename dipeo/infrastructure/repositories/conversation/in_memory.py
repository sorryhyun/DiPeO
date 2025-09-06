"""In-memory implementation of ConversationRepository."""

from typing import Any

from dipeo.diagram_generated import Message, PersonID
from dipeo.domain.conversation import Conversation
from dipeo.domain.conversation.ports import ConversationRepository


class InMemoryConversationRepository(ConversationRepository):
    """In-memory implementation of ConversationRepository.

    This implementation maintains a single global conversation
    in memory during execution.
    """

    def __init__(self):
        self._global_conversation = Conversation()

    def get_global_conversation(self) -> Conversation:
        """Get the global conversation shared by all persons."""
        return self._global_conversation

    def add_message(
        self, message: Message, execution_id: str | None = None, node_id: str | None = None
    ) -> None:
        """Add a message to the global conversation.

        Args:
            message: The message to add
            execution_id: Optional execution context (for future use)
            node_id: Optional node context (for future use)
        """
        # Add metadata if provided
        if execution_id or node_id:
            if not message.metadata:
                message.metadata = {}
            if execution_id:
                message.metadata["execution_id"] = execution_id
            if node_id:
                message.metadata["node_id"] = node_id

        self._global_conversation.add_message(message)

    def get_messages(self) -> list[Message]:
        """Get all messages from the global conversation."""
        return self._global_conversation.messages.copy()

    def get_conversation_history(self, person_id: PersonID) -> list[dict[str, Any]]:
        """Get conversation history for a specific person.

        Returns messages formatted for the person's perspective.
        """
        history = []
        for msg in self._global_conversation.messages:
            # Only include messages involving this person
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
        """Clear all messages from the conversation."""
        self._global_conversation.clear()

    def clear_person_messages(self, person_id: PersonID) -> None:
        """Clear all messages involving a specific person.

        This filters out messages from/to the specified person.
        """
        # Filter out messages involving this person
        filtered_messages = [
            msg
            for msg in self._global_conversation.messages
            if msg.from_person_id != person_id and msg.to_person_id != person_id
        ]

        # Clear and rebuild conversation with filtered messages
        self._global_conversation.clear()
        for msg in filtered_messages:
            self._global_conversation.add_message(msg)

    def get_message_count(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self._global_conversation.messages)

    def get_latest_message(self) -> Message | None:
        """Get the most recent message, if any."""
        return self._global_conversation.get_latest_message()
