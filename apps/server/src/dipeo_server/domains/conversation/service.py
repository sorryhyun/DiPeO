import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Any

from dipeo_core import BaseService, SupportsMemory

from .conversation import Message, PersonConversation


class ConversationService(BaseService, SupportsMemory):
    """Service for managing conversations between persons (LLM agents) that implements the SupportsMemory protocol."""

    def __init__(self, redis_url: str | None = None, message_store=None):
        super().__init__()
        self.person_conversations: dict[str, PersonConversation] = {}
        self.all_messages: OrderedDict[str, Message] = OrderedDict()
        self.execution_metadata: dict[str, dict[str, Any]] = {}
        self.message_store = message_store
        self._pending_persistence: dict[str, list[Message]] = {}

        self.MAX_GLOBAL_MESSAGES = 10000

    async def initialize(self) -> None:
        """Initialize the conversation service."""
        # Service is already initialized in __init__
        pass

    def _store_message(self, message: Message) -> None:
        self.all_messages[message.id] = message

        while len(self.all_messages) > self.MAX_GLOBAL_MESSAGES:
            self.all_messages.popitem(last=False)

    def _get_message(self, message_id: str) -> Message | None:
        return self.all_messages.get(message_id)

    def get_or_create_person_conversation(self, person_id: str) -> PersonConversation:
        if person_id not in self.person_conversations:
            self.person_conversations[person_id] = PersonConversation(
                person_id=person_id
            )
        return self.person_conversations[person_id]

    def add_message_to_conversation(
        self,
        content: str,
        sender_person_id: str,
        execution_id: str,
        participant_person_ids: list[str],
        role: str = "assistant",
        node_id: str | None = None,
        node_label: str | None = None,
        token_count: int | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cached_tokens: int | None = None,
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
            person_conversation = self.get_or_create_person_conversation(person_id)
            person_conversation.add_message(message)

        # Queue for deferred persistence
        if execution_id not in self._pending_persistence:
            self._pending_persistence[execution_id] = []
        self._pending_persistence[execution_id].append(message)

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
        self, person_id: str, execution_id: str | None = None
    ) -> None:
        """Make a person forget messages."""
        person_conversation = self.get_or_create_person_conversation(person_id)

        if execution_id:
            person_conversation.forget_messages_from_execution(execution_id)
        else:
            for message in person_conversation.messages:
                person_conversation.forgotten_message_ids.add(message.id)

    def forget_own_messages_for_person(
        self, person_id: str, execution_id: str | None = None
    ) -> None:
        """Make a person forget only their own messages."""
        person_conversation = self.get_or_create_person_conversation(person_id)

        if execution_id:
            person_conversation.forget_own_messages_from_execution(execution_id)
        else:
            person_conversation.forget_own_messages()

    def get_conversation_for_person(self, person_id: str) -> list[dict[str, Any]]:
        """Get all visible messages for a person."""
        person_conversation = self.get_or_create_person_conversation(person_id)
        return person_conversation.get_visible_messages(person_id)

    def get_execution_metadata(self, execution_id: str) -> dict[str, Any] | None:
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

    def get_conversation_stats(self) -> dict[str, Any]:
        """Get statistics about conversation usage."""
        return {
            "total_messages": len(self.all_messages),
            "active_persons": len(self.person_conversations),
            "active_executions": len(self.execution_metadata),
            "person_message_counts": {
                person_id: len(conversation.messages)
                for person_id, conversation in self.person_conversations.items()
            },
        }

    def clear_all_conversations(self) -> None:
        """Clear all conversation history for all persons."""
        self.person_conversations.clear()
        self.all_messages.clear()
        self.execution_metadata.clear()
        self._pending_persistence.clear()

    async def persist_execution_conversations(self, execution_id: str) -> None:
        """Persist all pending conversations for an execution."""
        if execution_id in self._pending_persistence:
            messages = self._pending_persistence.pop(execution_id)
            if self.message_store and messages:
                # Group messages by node_id for batch storage
                messages_by_node: dict[str, list[Message]] = {}
                for msg in messages:
                    if msg.node_id:
                        if msg.node_id not in messages_by_node:
                            messages_by_node[msg.node_id] = []
                        messages_by_node[msg.node_id].append(msg)

                # Store messages for each node
                for node_id, node_messages in messages_by_node.items():
                    conversation = [msg.to_dict() for msg in node_messages]
                    await self.message_store.store_message(
                        execution_id=execution_id,
                        node_id=node_id,
                        content={"conversation": conversation},
                        person_id=node_messages[0].sender_person_id,
                        token_count=sum(msg.token_count or 0 for msg in node_messages),
                    )

    # Protocol compliance methods (SupportsMemory)
    def get_or_create_person_memory(self, person_id: str) -> PersonConversation:
        """Get or create person memory - alias for get_or_create_person_conversation."""
        return self.get_or_create_person_conversation(person_id)

    def get_conversation_history(
        self, person_id: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Get conversation history for a person."""
        conversation = self.get_conversation_for_person(person_id)
        if limit:
            return conversation[-limit:]
        return conversation

    async def save_conversation_log(
        self,
        execution_id: str,
        node_id: str,
        conversation: list[dict[str, Any]],
        person_id: str,
        token_count: int = 0,
    ) -> None:
        """Save conversation log for a specific execution and node."""
        # Create messages from conversation data
        for msg_data in conversation:
            message = Message(
                id=msg_data.get("id", str(uuid.uuid4())),
                role=msg_data.get("role", "assistant"),
                content=msg_data.get("content", ""),
                timestamp=msg_data.get("timestamp", datetime.now()),
                sender_person_id=person_id,
                execution_id=execution_id,
                node_id=node_id,
                token_count=msg_data.get("token_count", 0),
            )
            self._store_message(message)

            # Queue for deferred persistence
            if execution_id not in self._pending_persistence:
                self._pending_persistence[execution_id] = []
            self._pending_persistence[execution_id].append(message)

        # Persist immediately if message store is available
        if self.message_store:
            await self.message_store.store_message(
                execution_id=execution_id,
                node_id=node_id,
                content={"conversation": conversation},
                person_id=person_id,
                token_count=token_count,
            )
