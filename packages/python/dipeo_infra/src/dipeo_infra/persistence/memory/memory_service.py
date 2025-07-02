"""Simple in-memory implementation of the SupportsMemory protocol."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from dipeo_core import SupportsMemory


class MemoryService(SupportsMemory):
    """In-memory conversation storage for local execution."""

    def __init__(self):
        # Structure: {person_id: {execution_id: [messages]}}
        self._conversations: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # Structure: {person_id: memory_object}
        self._person_memory: Dict[str, Any] = {}

    def get_or_create_person_memory(self, person_id: str) -> Any:
        """Create or retrieve memory for a specific person."""
        if person_id not in self._person_memory:
            self._person_memory[person_id] = {
                "id": person_id,
                "created_at": datetime.now().isoformat(),
                "conversations": [],
            }
        return self._person_memory[person_id]

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
        """Add a message to a person's conversation history."""
        if timestamp is None:
            timestamp = datetime.now().timestamp()

        # Determine message type
        if current_person_id == "system":
            message_type = "system_to_person"
        elif person_id == "system":
            message_type = "person_to_system"
        else:
            message_type = "person_to_person"

        message = {
            "role": role,
            "content": content,
            "from_person_id": current_person_id,
            "to_person_id": person_id,
            "message_type": message_type,
            "node_id": node_id,
            "timestamp": timestamp,
            "execution_id": execution_id,
        }

        self._conversations[person_id][execution_id].append(message)

        # Update person memory
        memory = self.get_or_create_person_memory(person_id)
        if execution_id not in [
            conv["execution_id"] for conv in memory.get("conversations", [])
        ]:
            memory["conversations"].append(
                {
                    "execution_id": execution_id,
                    "started_at": datetime.fromtimestamp(timestamp).isoformat(),
                }
            )

    def forget_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """Clear memory for a person, optionally for a specific execution."""
        if execution_id:
            if (
                person_id in self._conversations
                and execution_id in self._conversations[person_id]
            ):
                del self._conversations[person_id][execution_id]
        else:
            if person_id in self._conversations:
                del self._conversations[person_id]
            if person_id in self._person_memory:
                del self._person_memory[person_id]

    def forget_own_messages_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """Clear only the person's own messages from memory."""
        if person_id not in self._conversations:
            return

        if execution_id:
            if execution_id in self._conversations[person_id]:
                self._conversations[person_id][execution_id] = [
                    msg
                    for msg in self._conversations[person_id][execution_id]
                    if msg.get("from_person_id") != person_id
                ]
        else:
            for exec_id in self._conversations[person_id]:
                self._conversations[person_id][exec_id] = [
                    msg
                    for msg in self._conversations[person_id][exec_id]
                    if msg.get("from_person_id") != person_id
                ]

    def get_conversation_history(self, person_id: str) -> List[Dict[str, Any]]:
        """Retrieve the conversation history for a person."""
        if person_id not in self._conversations:
            return []

        # Combine all conversations for the person
        all_messages = []
        for execution_id, messages in self._conversations[person_id].items():
            all_messages.extend(messages)

        # Sort by timestamp
        all_messages.sort(key=lambda x: x.get("timestamp", 0))
        return all_messages

    async def save_conversation_log(self, execution_id: str, log_dir: Path) -> str:
        """Save conversation logs to a directory."""
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Collect all conversations for this execution
        conversations_data = {}
        for person_id, executions in self._conversations.items():
            if execution_id in executions:
                conversations_data[person_id] = executions[execution_id]

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"conversation_{execution_id}_{timestamp}.json"

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "execution_id": execution_id,
                    "timestamp": timestamp,
                    "conversations": conversations_data,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        return str(log_file)

    def clear_all_conversations(self) -> None:
        """Clear all conversations from memory."""
        self._conversations.clear()
        self._person_memory.clear()
