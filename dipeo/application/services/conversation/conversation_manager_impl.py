"""Implementation of ConversationManager protocol that bridges existing infrastructure."""

from typing import Any

from dipeo.application.protocols import SupportsMemory
from dipeo.core.dynamic.conversation import Conversation
from dipeo.core.dynamic.conversation_manager import ConversationManager
from dipeo.models import ForgettingMode, Message


class ConversationManagerImpl(ConversationManager):
    """ConversationManager implementation that bridges with existing memory infrastructure."""
    
    def __init__(self, memory_service: SupportsMemory):
        """Initialize with existing memory service.
        
        Args:
            memory_service: The existing SupportsMemory implementation
        """
        self.memory_service = memory_service
        self._conversations: dict[str, Conversation] = {}
        self._current_execution_id: str | None = None
    
    def get_conversation(self, person_id: str) -> Conversation:
        """Get the conversation for a specific person."""
        if person_id not in self._conversations:
            self._conversations[person_id] = self.create_conversation(person_id)
            self._load_existing_messages(person_id)
        return self._conversations[person_id]
    
    def create_conversation(self, person_id: str) -> Conversation:
        """Create a new conversation for a person."""
        conversation = Conversation()
        self._conversations[person_id] = conversation
        return conversation
    
    def add_message(
        self,
        person_id: str,
        message: Message,
        execution_id: str,
        node_id: str | None = None
    ) -> None:
        """Add a message to a person's conversation."""
        # Update current execution ID
        self._current_execution_id = execution_id
        
        # Get or create conversation
        conversation = self.get_conversation(person_id)
        
        # Add to new conversation object
        conversation.add_message(message)
        
        # Also add to legacy memory service for backward compatibility
        self.memory_service.add_message_to_conversation(
            person_id=person_id,
            execution_id=execution_id,
            role=self._get_role_from_message(message),
            content=message.content,
            current_person_id=message.from_person_id if isinstance(message.from_person_id, str) else "system",
            node_id=node_id,
            timestamp=message.timestamp
        )
    
    def apply_forgetting(
        self,
        person_id: str,
        mode: ForgettingMode,
        execution_id: str | None = None
    ) -> int:
        """Apply a forgetting strategy to a person's conversation."""
        execution_id = execution_id or self._current_execution_id
        
        if mode == ForgettingMode.on_every_turn:
            # Get conversation
            conversation = self.get_conversation(person_id)
            original_count = len(conversation.messages)
            
            # Filter out messages sent by this person
            filtered_messages = [
                msg for msg in conversation.messages
                if msg.from_person_id != person_id
            ]
            
            # Clear and rebuild conversation
            conversation.clear()
            for msg in filtered_messages:
                conversation.add_message(msg)
            
            # Update legacy memory service
            self.memory_service.forget_own_messages_for_person(person_id, execution_id)
            
            return original_count - len(filtered_messages)
        
        elif mode == ForgettingMode.upon_request:
            # Clear all messages
            conversation = self.get_conversation(person_id)
            count = len(conversation.messages)
            conversation.clear()
            
            # Update legacy memory service
            self.memory_service.forget_for_person(person_id, execution_id)
            
            return count
        
        return 0
    
    def merge_conversations(
        self,
        source_person_id: str,
        target_person_id: str
    ) -> None:
        """Merge one person's conversation into another's."""
        source_conv = self.get_conversation(source_person_id)
        target_conv = self.get_conversation(target_person_id)
        
        # Copy all messages from source to target
        for message in source_conv.messages:
            target_conv.add_message(message)
        
        # Note: Legacy memory service doesn't have a merge method,
        # so we'll need to handle this through message copying
        if self._current_execution_id:
            for msg in source_conv.messages:
                self.memory_service.add_message_to_conversation(
                    person_id=target_person_id,
                    execution_id=self._current_execution_id,
                    role=self._get_role_from_message(msg),
                    content=msg.content,
                    current_person_id=msg.from_person_id if isinstance(msg.from_person_id, str) else "system",
                    timestamp=msg.timestamp
                )
    
    def clear_conversation(
        self,
        person_id: str,
        execution_id: str | None = None
    ) -> None:
        """Clear a person's conversation history."""
        execution_id = execution_id or self._current_execution_id
        
        # Clear new conversation object
        if person_id in self._conversations:
            self._conversations[person_id].clear()
        
        # Clear legacy memory
        self.memory_service.forget_for_person(person_id, execution_id)
    
    def get_all_conversations(self) -> dict[str, Conversation]:
        """Get all active conversations."""
        return self._conversations.copy()
    
    # Helper methods
    
    def _load_existing_messages(self, person_id: str) -> None:
        """Load existing messages from memory service into conversation object."""
        history = self.memory_service.get_conversation_history(person_id)
        conversation = self._conversations[person_id]
        
        if history is None:
            return
        
        for msg_dict in history:
            # Convert legacy format to Message object
            message = self._dict_to_message(msg_dict, person_id)
            if message:
                conversation.add_message(message)
    
    def _dict_to_message(self, msg_dict: dict[str, Any], person_id: str) -> Message | None:
        """Convert legacy message dictionary to Message object."""
        # Skip if not from current execution
        if self._current_execution_id and msg_dict.get("execution_id") != self._current_execution_id:
            return None
        
        # Determine message type and IDs
        from_person_id = msg_dict.get("from_person_id", msg_dict.get("current_person_id", person_id))
        to_person_id = msg_dict.get("to_person_id", person_id)
        
        # Handle role mapping
        role = msg_dict.get("role", "user")
        if role == "system":
            from_person_id = "system"
            message_type = "system_to_person"
        elif role == "external":
            message_type = "person_to_person"
        else:
            message_type = "person_to_person"
        
        return Message(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            content=msg_dict.get("content", ""),
            timestamp=msg_dict.get("timestamp"),
            message_type=message_type,
            metadata={"role": role, "node_id": msg_dict.get("node_id")}
        )
    
    def _get_role_from_message(self, message: Message) -> str:
        """Extract role from Message object for legacy compatibility."""
        if message.from_person_id == "system":
            return "system"
        elif message.from_person_id == message.to_person_id:
            return "assistant"
        else:
            return "user"
    
    def set_execution_id(self, execution_id: str) -> None:
        """Set the current execution ID for the manager."""
        self._current_execution_id = execution_id