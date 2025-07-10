# Simplified conversation memory service focused on essential features.

from typing import Any, Dict, List, Optional

from dipeo.core import BaseService
from dipeo.application.protocols import SupportsMemory
from dipeo.core.utils import is_conversation
from dipeo.utils.conversation import OnEveryTurnHandler


class ConversationMemoryService(BaseService, SupportsMemory):
    """Conversation memory service with enhanced functionality.
    
    This service implements SupportsMemory to maintain protocol compatibility
    while providing additional conversation-specific methods. Some methods are
    simple pass-throughs to the underlying memory service to fulfill the protocol
    requirements, while others add conversation-specific business logic.
    
    Pass-through methods (required by SupportsMemory protocol):
    - get_or_create_person_memory
    - get_conversation_history  
    - clear_all_conversations
    - save_conversation_log
    
    Enhanced methods with business logic:
    - add_message: Simplified message adding
    - get_messages: Filtered message retrieval
    - prepare_messages_for_llm: LLM-compatible formatting
    - get_messages_for_output: Output formatting with forget modes
    - rebuild_conversation_context: Context reconstruction
    """

    def __init__(self, memory_service: SupportsMemory):
        super().__init__()
        self.memory_service = memory_service
        self.current_execution_id: Optional[str] = None

    async def initialize(self) -> None:
        pass

    def register_person(self, person_id: str, config: Dict[str, Any]) -> None:
        """Register a person's configuration.
        
        Args:
            person_id: The unique identifier for the person
            config: Configuration dictionary containing person settings
        """
        # Delegate to memory service if it supports registration
        if hasattr(self.memory_service, 'register_person'):
            self.memory_service.register_person(person_id, config)

    def get_person_config(self, person_id: str) -> Optional[Dict[str, Any]]:
        """Get a person's configuration.
        
        Args:
            person_id: The unique identifier for the person
            
        Returns:
            The person's configuration if registered, None otherwise
        """
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
        node_id: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Main method to add a message. Delegates to memory service."""
        # Store current execution ID for other methods to use
        if execution_id:
            self.current_execution_id = execution_id
        
        # Delegate to memory service
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

    def get_messages(self, person_id: str) -> List[Dict[str, str]]:
        """Get messages for a person from the memory service."""
        if not self.current_execution_id:
            return []
        
        # Get conversation history from memory service
        history = self.memory_service.get_conversation_history(person_id)
        
        # Filter by current execution and format for output
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
        """Clear messages with fine-grained control over which roles to keep.
        
        By default keeps all messages. Set parameters to False to clear specific roles.
        """
        # For now, use forget_for_person if we need to clear everything
        # In the future, this could be enhanced to support role-based clearing
        if not keep_system and not keep_user and not keep_assistant and not keep_external:
            self.memory_service.forget_for_person(person_id, self.current_execution_id)
        elif not keep_assistant:
            # Special case for clearing only assistant messages
            self.memory_service.forget_own_messages_for_person(person_id, self.current_execution_id)

    def get_or_create_person_memory(self, person_id: str) -> Any:
        # Delegate to memory service
        return self.memory_service.get_or_create_person_memory(person_id)

    def get_conversation_history(self, person_id: str) -> List[Dict[str, Any]]:
        # Interface method - delegates to memory service
        return self.memory_service.get_conversation_history(person_id)

    def forget_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        # Interface method - delegate to memory service
        self.memory_service.forget_for_person(person_id, execution_id or self.current_execution_id)

    def forget_own_messages_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """[DOMAIN LOGIC] Remove messages sent by the person, keeping received messages.
        
        This implements the business rule for "on_every_turn" forgetting mode where
        a person should not see their own previous responses in debates/conversations.
        """
        execution_id = execution_id or self.current_execution_id
        if not execution_id:
            return
        
        # Get all messages for the person
        history = self.memory_service.get_conversation_history(person_id)
        
        # Filter out messages sent by the person (from_person_id == person_id)
        messages_to_keep = []
        messages_to_remove = []
        
        for msg in history:
            if msg.get("execution_id") == execution_id:
                if msg.get("from_person_id") != person_id:
                    messages_to_keep.append(msg)
                else:
                    messages_to_remove.append(msg)
        
        # Clear and rebuild with only received messages
        if messages_to_remove:  # Only rebuild if there were messages to remove
            self.memory_service.forget_for_person(person_id, execution_id)
            
            # Re-add only the messages we want to keep
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
        # Delegate to memory service
        self.memory_service.clear_all_conversations()

    async def save_conversation_log(self, execution_id: str, log_dir: any) -> str:
        # Delegate to memory service
        return await self.memory_service.save_conversation_log(execution_id, log_dir)
    
    def get_messages_for_output(self, person_id: str, forget_mode: Optional[str] = None) -> List[Dict[str, str]]:
        """Get messages to pass to downstream nodes, respecting forgetting mode.
        
        For debate-style interactions with on_every_turn mode:
        - We need to get messages from OTHER persons (not the current person's own messages)
        - This requires checking the raw conversation history with metadata
        """
        
        if forget_mode == "on_every_turn":
            # Get raw conversation history with metadata
            if not self.current_execution_id:
                return []
                
            history = self.memory_service.get_conversation_history(person_id)
            
            # Use centralized handler for filtering
            return OnEveryTurnHandler.filter_messages_for_output(
                history, person_id, self.current_execution_id
            )
        
        # For other modes, return all messages (simplified format)
        return self.get_messages(person_id)
    
    def prepare_messages_for_llm(self, person_id: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Prepare messages for LLM call, handling external role conversion."""
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation messages, converting external to system
        for msg in self.get_messages(person_id):
            # Convert external messages to system role for LLM compatibility
            role = "system" if msg["role"] == "external" else msg["role"]
            messages.append({"role": role, "content": msg["content"]})
        
        return messages
    
    
    
    def get_messages_with_person_id(self, person_id: str, forget_mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get messages for output with person_id attached."""
        messages = self.get_messages_for_output(person_id, forget_mode)
        
        # Add personId to each message
        messages_with_id = []
        for msg in messages:
            msg_with_person = msg.copy()
            msg_with_person["person_id"] = person_id
            messages_with_id.append(msg_with_person)
        
        return messages_with_id
    
    def is_conversation(self, value: Any) -> bool:
        """Check if a value is a conversation (list of messages)."""
        return is_conversation(value)
    
    def rebuild_conversation_context(
        self, 
        person_id: str, 
        conversation_messages: List[Dict[str, Any]], 
        clear_existing: bool = True,
        forget_mode: Optional[str] = None
    ) -> None:
        """Rebuild conversation context from passed messages.
        
        Args:
            person_id: The person ID to rebuild conversation for
            conversation_messages: List of message dictionaries
            clear_existing: Whether to clear existing messages first
            forget_mode: The forget mode of the receiving person (e.g., "on_every_turn")
        """
        if not isinstance(conversation_messages, list):
            return
        
        # Clear existing conversation if requested
        if clear_existing:
            self.memory_service.forget_for_person(person_id, execution_id=self.current_execution_id)
        
        # Use centralized handler for filtering if needed
        conversation_messages = OnEveryTurnHandler.filter_rebuild_messages(
            conversation_messages, person_id, forget_mode
        )
        
        # Add messages to conversation history
        for msg in conversation_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # If this is an assistant message from another person, format it as a user message
            # with the person's label for proper context
            if role == "assistant" and msg.get("person_id") and msg.get("person_id") != person_id:
                # This is from another person, format with their label
                sender_id = msg.get("person_id")
                sender_label = msg.get("person_label", sender_id)  # Use label if available, fallback to ID
                content = f"[{sender_label}]: {content}"
                role = "user"
            
            self.add_message_to_conversation(
                person_id=person_id,
                execution_id=self.current_execution_id or "",
                role=role,
                content=content,
                current_person_id=person_id
            )