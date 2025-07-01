"""Simplified conversation memory service focused on essential features."""

from typing import Dict, List, Optional

from dipeo_core import BaseService, SupportsMemory


class ConversationMemoryService(BaseService, SupportsMemory):
    """Minimal conversation memory for person_job nodes."""

    def __init__(self):
        super().__init__()
        # Simple structure: {person_id: [messages]}
        self._conversations: Dict[str, List[Dict[str, str]]] = {}

    async def initialize(self) -> None:
        """Initialize the service - required by BaseService."""
        pass

    def add_message(self, person_id: str, role: str, content: str) -> None:
        """Add a message to person's conversation.
        
        Supported roles:
        - 'system': System prompts from person configuration
        - 'user': User prompts from node configuration
        - 'assistant': LLM responses
        - 'external': Input from other nodes (DB, API, etc.)
        """
        if person_id not in self._conversations:
            self._conversations[person_id] = []

        self._conversations[person_id].append({"role": role, "content": content})

    def get_messages(self, person_id: str) -> List[Dict[str, str]]:
        """Get all messages for a person."""
        return self._conversations.get(person_id, [])

    def clear_messages(self, person_id: str, keep_system: bool = True) -> None:
        """Clear messages for forgetting feature."""
        if person_id not in self._conversations:
            return

        if keep_system:
            # Keep only system messages
            self._conversations[person_id] = [
                msg for msg in self._conversations[person_id] if msg["role"] == "system"
            ]
        else:
            self._conversations[person_id] = []

    def clear_own_messages(self, person_id: str) -> None:
        """Remove assistant messages for 'on_every_turn' forgetting."""
        if person_id not in self._conversations:
            return

        self._conversations[person_id] = [
            msg for msg in self._conversations[person_id] if msg["role"] != "assistant"
        ]

    # Implement SupportsMemory protocol methods
    def get_or_create_person_memory(self, person_id: str) -> None:
        """Get or create person memory - implements SupportsMemory protocol."""
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
        """Add a message to conversation - implements SupportsMemory protocol."""
        self.add_message(person_id, role, content)

    def get_conversation_history(self, person_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a person - implements SupportsMemory protocol."""
        return self.get_messages(person_id)

    def forget_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """Clear conversation history - implements SupportsMemory protocol."""
        self.clear_messages(person_id, keep_system=False)

    def forget_own_messages_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """Remove messages sent by this person - implements SupportsMemory protocol."""
        self.clear_own_messages(person_id)

    def clear_all_conversations(self) -> None:
        """Clear all conversation history for all persons."""
        self._conversations.clear()

    async def save_conversation_log(self, execution_id: str, log_dir: any) -> str:
        """Save conversation log to file - implements SupportsMemory protocol."""
        # Simple implementation - just return a dummy path
        return f"{log_dir}/conversation_{execution_id}.json"
