"""In-memory storage implementation for conversation data.

This module provides the infrastructure layer implementation for conversation storage,
following the SupportsMemory protocol. It handles low-level storage operations without
business logic, which should be implemented in the domain layer instead.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from dipeo.application.protocols import SupportsMemory


class InMemoryConversationStore(SupportsMemory):
    """In-memory storage for conversation data (infrastructure layer).
    
    This class provides pure storage operations for conversation messages without
    business logic. It implements the SupportsMemory protocol to store and retrieve
    conversation data during diagram execution.
    
    Responsibilities (infrastructure layer):
    - Store and retrieve messages
    - Clear stored data
    - Save conversation logs to disk
    
    NOT responsible for (domain layer concerns):
    - Forgetting strategies
    - Message filtering logic
    - Conversation context rebuilding
    
    Attributes:
        _conversations: Nested dictionary storing conversations by person_id and execution_id
        _person_configs: Dictionary storing person configurations
    """

    def __init__(self):
        # Structure: {person_id: {execution_id: [messages]}}
        self._conversations: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # Store person configurations
        self._person_configs: dict[str, dict[str, Any]] = {}

    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Register a person's configuration.
        
        Args:
            person_id: The unique identifier for the person
            config: Configuration dictionary containing person settings like name, model, etc.
        """
        self._person_configs[person_id] = config

    def get_person_config(self, person_id: str) -> dict[str, Any] | None:
        """Get a person's configuration.
        
        Args:
            person_id: The unique identifier for the person
            
        Returns:
            The person's configuration if registered, None otherwise
        """
        return self._person_configs.get(person_id)

    def get_or_create_person_memory(self, person_id: str) -> Any:
        """Create or retrieve memory for a specific person.
        
        Args:
            person_id: The unique identifier for the person
            
        Returns:
            The memory object for the person, containing id, created_at, and conversations
        """
        # This method is kept for backward compatibility but simplified
        # The actual conversation data is stored in _conversations
        conversations_list = []
        if person_id in self._conversations:
            for exec_id, messages in self._conversations[person_id].items():
                if messages:
                    conversations_list.append({
                        "execution_id": exec_id,
                        "started_at": datetime.fromtimestamp(messages[0]["timestamp"]).isoformat()
                    })
        
        return {
            "id": person_id,
            "created_at": datetime.now().isoformat(),
            "conversations": conversations_list,
        }

    def add_message_to_conversation(
        self,
        person_id: str,
        execution_id: str,
        role: str,
        content: str,
        current_person_id: str,
        node_id: str | None = None,
        timestamp: float | None = None,
    ) -> None:
        """Add a message to a person's conversation history.
        
        Args:
            person_id: The ID of the person receiving the message
            execution_id: The execution context ID
            role: The role of the message (e.g., 'user', 'assistant')
            content: The message content
            current_person_id: The ID of the person sending the message
            node_id: Optional node ID associated with this message
            timestamp: Optional timestamp (defaults to current time)
        """
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

    def forget_for_person(
        self, person_id: str, execution_id: str | None = None
    ) -> None:
        """Clear all stored messages for a person (infrastructure operation).
        
        This is a pure storage operation that removes data. It does not contain
        business logic about when or why to forget - that belongs in the domain layer.
        
        Args:
            person_id: The ID of the person whose messages to clear
            execution_id: Optional execution ID to clear messages for specific execution only
        """
        if execution_id:
            if (
                person_id in self._conversations
                and execution_id in self._conversations[person_id]
            ):
                del self._conversations[person_id][execution_id]
        else:
            if person_id in self._conversations:
                del self._conversations[person_id]

    def forget_own_messages_for_person(
        self, person_id: str, execution_id: str | None = None
    ) -> None:
        """[DEPRECATED] This method is kept for protocol compatibility only.
        
        The filtering logic has been moved to the domain layer where it belongs.
        This infrastructure method now does nothing - the domain layer handles
        the business logic of filtering messages.
        
        Args:
            person_id: The ID of the person (ignored)
            execution_id: Optional execution ID (ignored)
        """
        # No-op: Business logic moved to domain layer
        # Domain services now handle message filtering based on business rules
        pass

    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        """Retrieve the conversation history for a person.
        
        Args:
            person_id: The ID of the person whose conversation history to retrieve
            
        Returns:
            List of messages sorted by timestamp, combining all executions
        """
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
        """Save conversation logs to a directory.
        
        Args:
            execution_id: The execution ID to save logs for
            log_dir: The directory path to save logs to
            
        Returns:
            The path to the saved log file
        """
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
        """Clear all conversations from memory.
        
        This method removes all stored conversations and person memory objects,
        effectively resetting the service to its initial state.
        """
        self._conversations.clear()
        self._person_configs.clear()