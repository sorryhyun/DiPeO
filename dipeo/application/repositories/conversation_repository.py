"""In-memory implementation of ConversationRepository."""

from dipeo.diagram_generated import Message
from dipeo.domain.conversation import Conversation
from dipeo.domain.ports import ConversationRepository


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
    
    def add_message(self, message: Message) -> None:
        """Add a message to the global conversation."""
        self._global_conversation.add_message(message)
    
    def get_messages(self) -> list[Message]:
        """Get all messages from the global conversation."""
        return self._global_conversation.messages.copy()
    
    def clear(self) -> None:
        """Clear all messages from the conversation."""
        self._global_conversation.clear()
    
    def get_message_count(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self._global_conversation.messages)
    
    def get_latest_message(self) -> Message | None:
        """Get the most recent message, if any."""
        return self._global_conversation.get_latest_message()