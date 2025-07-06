# Simplified conversation memory service focused on essential features.

from typing import Any, Dict, List, Optional

from dipeo_core import BaseService, SupportsMemory


class ConversationMemoryService(BaseService, SupportsMemory):
    # Minimal conversation memory for person_job nodes.
    # Supports system, user, assistant, and external message roles.

    def __init__(self, memory_service: SupportsMemory):
        super().__init__()
        self.memory_service = memory_service
        self.current_execution_id: Optional[str] = None

    async def initialize(self) -> None:
        pass

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

    def _clear_messages(
        self, 
        person_id: str, 
        keep_system: bool = True,
        keep_user: bool = True,
        keep_assistant: bool = True,
        keep_external: bool = True
    ) -> None:
        """Internal method to clear messages with fine-grained control.
        
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
        # Interface method - delegate to memory service
        self.memory_service.forget_own_messages_for_person(person_id, execution_id or self.current_execution_id)

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
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"get_messages_for_output: person_id={person_id}, forget_mode={forget_mode}")
        
        if forget_mode == "on_every_turn":
            # Get raw conversation history with metadata
            if not self.current_execution_id:
                return []
                
            history = self.memory_service.get_conversation_history(person_id)
            
            # Filter messages from OTHER persons in current execution
            # Group by sender to get only the last message from each person
            last_messages_by_person = {}
            
            for msg in history:
                if msg.get("execution_id") != self.current_execution_id:
                    continue
                    
                # Check if this message is FROM another person TO this person
                from_person = msg.get("from_person_id")
                to_person = msg.get("to_person_id")
                
                # We want messages where someone else sent TO this person
                if to_person == person_id and from_person != person_id and from_person != "system":
                    if msg.get("role") == "assistant":
                        # This is a message from another person - keep only the latest
                        last_messages_by_person[from_person] = {
                            "role": msg.get("role"),
                            "content": msg.get("content", ""),
                            "from_person_id": from_person
                        }
                        logger.debug(f"Found message from {from_person} to {person_id}: {msg.get('content', '')[:50]}...")
            
            # Return the last message from each other person
            result = list(last_messages_by_person.values())
            logger.debug(f"Returning {len(result)} messages from other persons for {person_id}")
            return result
        
        # For other modes, return all messages (simplified format)
        messages = self.get_messages(person_id)
        logger.debug(f"Returning all {len(messages)} messages for {person_id}")
        return messages
    
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
        if not isinstance(value, list) or not value:
            return False
        
        # Check if all items look like messages
        return all(
            isinstance(item, dict) and 
            'role' in item and 
            'content' in item 
            for item in value
        )
    
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
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Rebuilding conversation for person_id={person_id}, messages count={len(conversation_messages)}, forget_mode={forget_mode}")
        
        # For on_every_turn mode, we should only process the incoming messages
        # The sender has already filtered to just their last assistant message
        if forget_mode == "on_every_turn":
            logger.debug(f"Using on_every_turn mode for {person_id}")
            # Filter out messages from the receiving person itself
            conversation_messages = [
                msg for msg in conversation_messages 
                if msg.get("person_id") != person_id
            ]
            logger.debug(f"Filtered messages to {len(conversation_messages)} from other persons")
        
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
                logger.debug(f"Message from {sender_label} (id={sender_id}) to {person_id}: {content[:100]}...")
                content = f"[{sender_label}]: {content}"
                role = "user"
            
            self.add_message_to_conversation(
                person_id=person_id,
                execution_id=self.current_execution_id or "",
                role=role,
                content=content,
                current_person_id=person_id
            )
    
    
