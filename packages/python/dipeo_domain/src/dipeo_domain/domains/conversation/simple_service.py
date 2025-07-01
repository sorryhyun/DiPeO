# Simplified conversation memory service focused on essential features.

from typing import Dict, List, Optional

from dipeo_core import BaseService, SupportsMemory


class ConversationMemoryService(BaseService, SupportsMemory):
    # Minimal conversation memory for person_job nodes.
    # Supports system, user, assistant, and external message roles.

    def __init__(self):
        super().__init__()
        # Simple structure: {person_id: [messages]}
        self._conversations: Dict[str, List[Dict[str, str]]] = {}

    async def initialize(self) -> None:
        pass

    def add_message(self, person_id: str, role: str, content: str) -> None:
        if person_id not in self._conversations:
            self._conversations[person_id] = []

        self._conversations[person_id].append({"role": role, "content": content})

    def get_messages(self, person_id: str) -> List[Dict[str, str]]:
        return self._conversations.get(person_id, [])

    def clear_messages(self, person_id: str, keep_system: bool = True) -> None:
        if person_id not in self._conversations:
            return

        if keep_system:
            self._conversations[person_id] = [
                msg for msg in self._conversations[person_id] if msg["role"] == "system"
            ]
        else:
            self._conversations[person_id] = []

    def clear_own_messages(self, person_id: str) -> None:
        if person_id not in self._conversations:
            return

        self._conversations[person_id] = [
            msg for msg in self._conversations[person_id] if msg["role"] != "assistant"
        ]

    def get_or_create_person_memory(self, person_id: str) -> None:
        if person_id not in self._conversations:
            self._conversations[person_id] = []

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
        self.add_message(person_id, role, content)

    def get_conversation_history(self, person_id: str) -> List[Dict[str, str]]:
        return self.get_messages(person_id)

    def forget_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        self.clear_messages(person_id, keep_system=False)

    def forget_own_messages_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        self.clear_own_messages(person_id)

    def clear_all_conversations(self) -> None:
        self._conversations.clear()

    async def save_conversation_log(self, execution_id: str, log_dir: any) -> str:
        return f"{log_dir}/conversation_{execution_id}.json"
