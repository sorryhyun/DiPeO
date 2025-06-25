import uuid
from collections import OrderedDict
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
class PersonMemory:
    """Memory state for a specific person with proper cleanup."""

    person_id: str
    messages: List[Message] = field(default_factory=list)
    forgotten_message_ids: set[str] = field(default_factory=set)
    last_execution_id: Optional[str] = None
    MAX_MESSAGES = 100

    def add_message(self, message: Message) -> None:
        """Add a message to memory with automatic cleanup of old messages."""
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


class MemoryService:
    def __init__(self, redis_url: Optional[str] = None):
        self.person_memories: Dict[str, PersonMemory] = {}
        self.all_messages: OrderedDict[str, Message] = OrderedDict()
        self.execution_metadata: Dict[str, Dict[str, Any]] = {}

        self.MAX_GLOBAL_MESSAGES = 10000

    def _store_message(self, message: Message) -> None:
        self.all_messages[message.id] = message

        while len(self.all_messages) > self.MAX_GLOBAL_MESSAGES:
            self.all_messages.popitem(last=False)

    def _get_message(self, message_id: str) -> Optional[Message]:
        return self.all_messages.get(message_id)

    def get_or_create_person_memory(self, person_id: str) -> PersonMemory:
        if person_id not in self.person_memories:
            self.person_memories[person_id] = PersonMemory(person_id=person_id)
        return self.person_memories[person_id]

    def add_message_to_conversation(
        self,
        content: str,
        sender_person_id: str,
        execution_id: str,
        participant_person_ids: List[str],
        role: str = "assistant",
        node_id: Optional[str] = None,
        node_label: Optional[str] = None,
        token_count: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cached_tokens: Optional[int] = None,
    ) -> Message:
        """Create and add message to conversation."""
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            sender_person_id=sender_person_id,
            execution_id=execution_id,
            node_id=node_id,
            node_label=node_label,
            token_count=token_count,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )

        self._store_message(message)

        for person_id in participant_person_ids:
            person_memory = self.get_or_create_person_memory(person_id)
            person_memory.add_message(message)

        if execution_id not in self.execution_metadata:
            self.execution_metadata[execution_id] = {
                "start_time": datetime.now(),
                "message_count": 0,
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
            }

        metadata = self.execution_metadata[execution_id]
        metadata["message_count"] += 1
        if token_count:
            metadata["total_tokens"] += token_count
        if input_tokens:
            metadata["input_tokens"] += input_tokens
        if output_tokens:
            metadata["output_tokens"] += output_tokens
        if cached_tokens:
            metadata["cached_tokens"] += cached_tokens

        return message

    def forget_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """Make a person forget messages."""
        person_memory = self.get_or_create_person_memory(person_id)

        if execution_id:
            person_memory.forget_messages_from_execution(execution_id)
        else:
            for message in person_memory.messages:
                person_memory.forgotten_message_ids.add(message.id)

    def forget_own_messages_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """Make a person forget only their own messages."""
        person_memory = self.get_or_create_person_memory(person_id)

        if execution_id:
            person_memory.forget_own_messages_from_execution(execution_id)
        else:
            person_memory.forget_own_messages()

    def get_conversation_for_person(self, person_id: str) -> List[Dict[str, Any]]:
        """Get all visible messages for a person."""
        person_memory = self.get_or_create_person_memory(person_id)
        return person_memory.get_visible_messages(person_id)

    def get_execution_metadata(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an execution."""
        return self.execution_metadata.get(execution_id)

    def cleanup_old_executions(self, max_age_hours: int = 24) -> int:
        """Clean up old execution metadata and return count of removed executions."""
        current_time = datetime.now()
        removed_count = 0

        execution_ids_to_remove = []
        for exec_id, metadata in self.execution_metadata.items():
            start_time = metadata.get("start_time")
            if (
                start_time
                and (current_time - start_time).total_seconds() > max_age_hours * 3600
            ):
                execution_ids_to_remove.append(exec_id)

        for exec_id in execution_ids_to_remove:
            del self.execution_metadata[exec_id]
            removed_count += 1

        return removed_count

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage."""
        return {
            "total_messages": len(self.all_messages),
            "active_persons": len(self.person_memories),
            "active_executions": len(self.execution_metadata),
            "person_message_counts": {
                person_id: len(memory.messages)
                for person_id, memory in self.person_memories.items()
            },
        }

    def clear_all_conversations(self) -> None:
        """Clear all conversation history for all persons."""
        self.person_memories.clear()
        self.all_messages.clear()
        self.execution_metadata.clear()


# MemoryService is already defined above
