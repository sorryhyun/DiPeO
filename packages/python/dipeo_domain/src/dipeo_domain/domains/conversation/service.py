import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dipeo_core import BaseService, SupportsMemory
from dipeo_domain.models import Message

from .models import PersonConversation


class ConversationMemoryDomainService(BaseService, SupportsMemory):
    """Service for managing conversations between persons (LLM agents)."""

    def __init__(self):
        super().__init__()
        self.person_conversations: dict[str, PersonConversation] = {}
        self.MAX_MESSAGES_PER_PERSON = 100

    async def initialize(self) -> None:
        """Initialize the conversation service."""
        pass

    def get_or_create_person_memory(self, person_id: str) -> PersonConversation:
        """Get or create person memory - implements SupportsMemory protocol."""
        if person_id not in self.person_conversations:
            self.person_conversations[person_id] = PersonConversation(
                person_id=person_id
            )
        return self.person_conversations[person_id]

    def add_message_to_conversation(
        self,
        person_id: str,
        execution_id: str,
        role: str,
        content: str,
        current_person_id: str,
        node_id: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Add a message to conversation - implements SupportsMemory protocol."""
        # Determine message type
        if current_person_id == "system":
            message_type = "system_to_person"
        elif person_id == "system":
            message_type = "person_to_system"
        else:
            message_type = "person_to_person"

        # Create message
        message = Message(
            id=str(uuid.uuid4()),
            from_person_id=current_person_id,
            to_person_id=person_id,
            content=content,
            timestamp=datetime.fromtimestamp(timestamp).isoformat()
            if timestamp
            else datetime.now().isoformat(),
            message_type=message_type,
            metadata={
                "execution_id": execution_id,
                "node_id": node_id,
            },
        )

        # Add to person's conversation
        conversation = self.get_or_create_person_memory(person_id)
        conversation.add_message(message)

        # Trim old messages if needed
        if len(conversation.messages) > self.MAX_MESSAGES_PER_PERSON:
            conversation.messages = conversation.messages[
                -self.MAX_MESSAGES_PER_PERSON :
            ]

    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        """Get conversation history for a person - implements SupportsMemory protocol."""
        conversation = self.get_or_create_person_memory(person_id)
        return [self._message_to_dict(msg, person_id) for msg in conversation.messages]

    def forget_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """Clear conversation history - implements SupportsMemory protocol."""
        conversation = self.get_or_create_person_memory(person_id)

        if execution_id:
            # Remove messages from specific execution
            conversation.messages = [
                msg
                for msg in conversation.messages
                if msg.metadata.get("execution_id") != execution_id
            ]
        else:
            # Clear all messages
            conversation.messages.clear()

    def forget_own_messages_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """Remove messages sent by this person - implements SupportsMemory protocol."""
        conversation = self.get_or_create_person_memory(person_id)

        # Filter out messages where this person was the sender
        conversation.messages = [
            msg
            for msg in conversation.messages
            if msg.from_person_id != person_id
            or (execution_id and msg.metadata.get("execution_id") != execution_id)
        ]

    def clear_all_conversations(self) -> None:
        """Clear all conversation history for all persons."""
        self.person_conversations.clear()

    async def save_conversation_log(self, execution_id: str, log_dir: Path) -> str:
        """Save conversation log to file - implements SupportsMemory protocol."""
        import json

        # Collect all messages for this execution
        execution_messages = []
        for person_id, conversation in self.person_conversations.items():
            for msg in conversation.messages:
                if msg.metadata.get("execution_id") == execution_id:
                    execution_messages.append(
                        {
                            "person_id": person_id,
                            "message": self._message_to_dict(msg, person_id),
                        }
                    )

        # Sort by timestamp
        execution_messages.sort(key=lambda x: x["message"]["timestamp"])

        # Save to file
        log_filename = f"conversation_{execution_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_path = log_dir / log_filename

        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w") as f:
            json.dump(
                {"execution_id": execution_id, "messages": execution_messages},
                f,
                indent=2,
                default=str,
            )

        return str(log_path)

    def _message_to_dict(
        self, message: Message, viewer_person_id: str
    ) -> dict[str, Any]:
        """Convert message to dict with dynamic role assignment."""
        # Dynamic role assignment based on viewer and message type
        if message.from_person_id == viewer_person_id:
            role = "assistant"  # Messages I sent
        elif (
            message.from_person_id == "system"
            or message.message_type == "system_to_person"
        ):
            role = "system"  # System messages
        else:
            role = "user"  # Messages from other persons

        return {
            "role": role,
            "content": message.content,
            "timestamp": message.timestamp
            if isinstance(message.timestamp, str)
            else message.timestamp.isoformat(),
            "personId": message.from_person_id,
            "messageType": message.message_type,
        }

    def get_conversation_for_person(self, person_id: str) -> list[dict[str, Any]]:
        """Get all visible messages for a person - backward compatibility."""
        return self.get_conversation_history(person_id)

    def get_or_create_person_conversation(self, person_id: str) -> PersonConversation:
        """Alias for get_or_create_person_memory - backward compatibility."""
        return self.get_or_create_person_memory(person_id)
