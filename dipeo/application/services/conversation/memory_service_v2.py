"""Enhanced conversation memory service that uses ConversationManager."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.protocols import SupportsMemory
from dipeo.core import BaseService
from dipeo.core.utils import is_conversation
from dipeo.models import ForgettingMode, Message, PersonID
from dipeo.utils.conversation import OnEveryTurnHandler

if TYPE_CHECKING:
    from dipeo.core.dynamic.conversation_manager import ConversationManager


class ConversationMemoryServiceV2(BaseService, SupportsMemory):
    """Enhanced conversation memory service using ConversationManager.
    
    This service maintains backward compatibility with SupportsMemory protocol
    while leveraging the new ConversationManager for improved conversation handling.
    """

    def __init__(
        self, 
        memory_service: SupportsMemory,
        conversation_manager: Optional["ConversationManager"] = None
    ):
        """Initialize with memory service and optional ConversationManager.
        
        Args:
            memory_service: Legacy memory service for backward compatibility
            conversation_manager: New conversation manager (optional)
        """
        super().__init__()
        self.memory_service = memory_service
        self.conversation_manager = conversation_manager
        self.current_execution_id: str | None = None
        
        # If conversation manager is provided, create an adapter
        if conversation_manager:
            from dipeo.application.services.conversation.conversation_manager_impl import (
                ConversationManagerImpl,
            )
            # Ensure the conversation manager is properly initialized
            if not isinstance(conversation_manager, ConversationManagerImpl):
                self.conversation_manager = ConversationManagerImpl(memory_service)
            else:
                self.conversation_manager = conversation_manager

    async def initialize(self) -> None:
        """Initialize the service."""
        pass

    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Register a person's configuration."""
        # Delegate to memory service
        if hasattr(self.memory_service, 'register_person'):
            self.memory_service.register_person(person_id, config)
        
        # Also create conversation in manager if available
        if self.conversation_manager:
            self.conversation_manager.create_conversation(person_id)

    def get_person_config(self, person_id: str) -> dict[str, Any] | None:
        """Get a person's configuration."""
        if hasattr(self.memory_service, 'get_person_config'):
            return self.memory_service.get_person_config(person_id)
        return None

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
        """Add a message to conversation using ConversationManager if available."""
        # Store current execution ID
        if execution_id:
            self.current_execution_id = execution_id
            if self.conversation_manager and hasattr(self.conversation_manager, 'set_execution_id'):
                self.conversation_manager.set_execution_id(execution_id)
        
        # Create Message object for ConversationManager
        if self.conversation_manager:
            # Determine from/to person IDs based on role
            if role == "system":
                from_person_id = "system"
                to_person_id = PersonID(person_id)
                message_type = "system_to_person"
            elif role == "assistant":
                from_person_id = PersonID(person_id)
                to_person_id = PersonID(current_person_id) if current_person_id != person_id else "system"
                message_type = "person_to_person" if current_person_id != person_id else "person_to_system"
            else:  # user or external
                from_person_id = PersonID(current_person_id) if current_person_id != person_id else "system"
                to_person_id = PersonID(person_id)
                message_type = "person_to_person" if current_person_id != person_id else "system_to_person"
            
            message = Message(
                from_person_id=from_person_id,
                to_person_id=to_person_id,
                content=content,
                message_type=message_type,
                timestamp=datetime.fromtimestamp(timestamp).isoformat() if timestamp else None,
                metadata={"role": role, "node_id": node_id}
            )
            
            self.conversation_manager.add_message(
                person_id=person_id,
                message=message,
                execution_id=execution_id,
                node_id=node_id
            )
        else:
            # Fallback to legacy memory service
            self.memory_service.add_message_to_conversation(
                person_id=person_id,
                execution_id=execution_id,
                role=role,
                content=content,
                current_person_id=current_person_id,
                node_id=node_id,
                timestamp=timestamp
            )
    
    def add_message(self, person_id: str, role: str, content: str) -> None:
        """Simplified method that delegates to add_message_to_conversation."""
        self.add_message_to_conversation(
            person_id=person_id,
            execution_id=self.current_execution_id or "",
            role=role,
            content=content,
            current_person_id=person_id
        )

    def get_messages(self, person_id: str) -> list[dict[str, str]]:
        """Get messages for a person using ConversationManager if available."""
        if self.conversation_manager and self.current_execution_id:
            conversation = self.conversation_manager.get_conversation(person_id)
            messages = []
            
            for msg in conversation.messages:
                # Convert Message objects to dict format
                if msg.from_person_id == person_id:
                    role = "assistant"
                elif msg.from_person_id == "system":
                    role = "system"
                else:
                    role = "user"
                
                messages.append({
                    "role": role,
                    "content": msg.content
                })
            
            return messages
        else:
            # Fallback to legacy method
            if not self.current_execution_id:
                return []
            
            history = self.memory_service.get_conversation_history(person_id)
            messages = []
            for msg in history:
                if msg.get("execution_id") == self.current_execution_id:
                    messages.append({
                        "role": msg.get("role", ""),
                        "content": msg.get("content", "")
                    })
            
            return messages

    def clear_messages(
        self, 
        person_id: str, 
        keep_system: bool = True,
        keep_user: bool = True,
        keep_assistant: bool = True,
        keep_external: bool = True
    ) -> None:
        """Clear messages with fine-grained control."""
        if not keep_system and not keep_user and not keep_assistant and not keep_external:
            if self.conversation_manager:
                self.conversation_manager.clear_conversation(person_id, self.current_execution_id)
            else:
                self.memory_service.forget_for_person(person_id, self.current_execution_id)
        elif not keep_assistant:
            # Special case for clearing only assistant messages
            if self.conversation_manager:
                self.conversation_manager.apply_forgetting(
                    person_id, 
                    ForgettingMode.on_every_turn,
                    self.current_execution_id
                )
            else:
                self.memory_service.forget_own_messages_for_person(person_id, self.current_execution_id)

    # SupportsMemory protocol methods
    
    def get_or_create_person_memory(self, person_id: str) -> Any:
        """Get or create person memory."""
        if self.conversation_manager:
            # Ensure conversation exists
            self.conversation_manager.get_conversation(person_id)
        return self.memory_service.get_or_create_person_memory(person_id)

    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        """Get conversation history."""
        if self.conversation_manager:
            conversation = self.conversation_manager.get_conversation(person_id)
            history = []
            
            for msg in conversation.messages:
                # Convert to legacy format
                history.append({
                    "role": "assistant" if msg.from_person_id == person_id else "user",
                    "content": msg.content,
                    "from_person_id": str(msg.from_person_id),
                    "to_person_id": str(msg.to_person_id),
                    "execution_id": self.current_execution_id,
                    "timestamp": msg.timestamp,
                    "node_id": msg.metadata.get("node_id") if msg.metadata else None
                })
            
            return history
        else:
            return self.memory_service.get_conversation_history(person_id)

    def forget_for_person(
        self, person_id: str, execution_id: str | None = None
    ) -> None:
        """Clear all messages for a person."""
        execution_id = execution_id or self.current_execution_id
        
        if self.conversation_manager:
            self.conversation_manager.clear_conversation(person_id, execution_id)
        else:
            self.memory_service.forget_for_person(person_id, execution_id)

    def forget_own_messages_for_person(
        self, person_id: str, execution_id: str | None = None
    ) -> None:
        """Remove messages sent by the person (on_every_turn mode)."""
        execution_id = execution_id or self.current_execution_id
        
        if self.conversation_manager:
            self.conversation_manager.apply_forgetting(
                person_id,
                ForgettingMode.on_every_turn,
                execution_id
            )
        else:
            # Fallback to legacy implementation
            if not execution_id:
                return
            
            history = self.memory_service.get_conversation_history(person_id)
            messages_to_keep = []
            
            for msg in history:
                if (
                    msg.get("execution_id") == execution_id
                    and msg.get("from_person_id") != person_id
                ):
                    messages_to_keep.append(msg)
            
            # Clear and rebuild
            self.memory_service.forget_for_person(person_id, execution_id)
            
            for msg in messages_to_keep:
                self.memory_service.add_message_to_conversation(
                    person_id=person_id,
                    execution_id=execution_id,
                    role=msg.get("role", ""),
                    content=msg.get("content", ""),
                    current_person_id=msg.get("from_person_id", ""),
                    node_id=msg.get("node_id"),
                    timestamp=msg.get("timestamp")
                )

    def clear_all_conversations(self) -> None:
        """Clear all conversations."""
        if self.conversation_manager:
            # Clear all conversations in manager
            all_conversations = self.conversation_manager.get_all_conversations()
            for person_id in all_conversations:
                self.conversation_manager.clear_conversation(person_id)
        
        # Also clear in legacy service
        self.memory_service.clear_all_conversations()

    async def save_conversation_log(self, execution_id: str, log_dir: any) -> str:
        """Save conversation log."""
        # For now, delegate to legacy service
        # In future, could use ConversationPersistence protocol
        return await self.memory_service.save_conversation_log(execution_id, log_dir)
    
    def get_messages_for_output(self, person_id: str, forget_mode: str | None = None) -> list[dict[str, str]]:
        """Get messages for output with forgetting mode applied."""
        if forget_mode == "on_every_turn":
            if self.conversation_manager and self.current_execution_id:
                conversation = self.conversation_manager.get_conversation(person_id)
                
                # Filter messages based on on_every_turn logic
                filtered_messages = []
                for msg in conversation.messages:
                    # Include messages NOT from this person
                    if msg.from_person_id != person_id:
                        role = "user" if msg.from_person_id != "system" else "system"
                        filtered_messages.append({
                            "role": role,
                            "content": msg.content
                        })
                
                return filtered_messages
            else:
                # Use legacy handler
                history = self.memory_service.get_conversation_history(person_id)
                return OnEveryTurnHandler.filter_messages_for_output(
                    history, person_id, self.current_execution_id
                )
        
        # For other modes, return all messages
        return self.get_messages(person_id)
    
    def prepare_messages_for_llm(self, person_id: str, system_prompt: str | None = None) -> list[dict[str, str]]:
        """Prepare messages for LLM call."""
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation messages
        for msg in self.get_messages(person_id):
            # Convert external to system for LLM compatibility
            role = "system" if msg["role"] == "external" else msg["role"]
            messages.append({"role": role, "content": msg["content"]})
        
        return messages
    
    def get_messages_with_person_id(self, person_id: str, forget_mode: str | None = None) -> list[dict[str, Any]]:
        """Get messages with person_id attached."""
        messages = self.get_messages_for_output(person_id, forget_mode)
        
        # Add personId to each message
        messages_with_id = []
        for msg in messages:
            msg_with_person = msg.copy()
            msg_with_person["person_id"] = person_id
            messages_with_id.append(msg_with_person)
        
        return messages_with_id
    
    def is_conversation(self, value: Any) -> bool:
        """Check if a value is a conversation."""
        return is_conversation(value)
    
    def rebuild_conversation_context(
        self, 
        person_id: str, 
        conversation_messages: list[dict[str, Any]], 
        clear_existing: bool = True,
        forget_mode: str | None = None
    ) -> None:
        """Rebuild conversation context from passed messages."""
        if not isinstance(conversation_messages, list):
            return
        
        # Clear existing if requested
        if clear_existing:
            self.forget_for_person(person_id, self.current_execution_id)
        
        # Filter messages if needed
        conversation_messages = OnEveryTurnHandler.filter_rebuild_messages(
            conversation_messages, person_id, forget_mode
        )
        
        # Add messages to conversation
        for msg in conversation_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Format content for multi-person conversations
            if role == "assistant" and msg.get("person_id") and msg.get("person_id") != person_id:
                sender_id = msg.get("person_id")
                sender_label = msg.get("person_label", sender_id)
                content = f"[{sender_label}]: {content}"
                role = "user"
            
            self.add_message_to_conversation(
                person_id=person_id,
                execution_id=self.current_execution_id or "",
                role=role,
                content=content,
                current_person_id=person_id
            )