"""Person dynamic object representing an LLM agent with evolving conversation state."""

from typing import Dict, Any, List, Optional, TYPE_CHECKING, Union

from dipeo.models import (
    PersonLLMConfig, Message, PersonID, ChatResult, 
    MemoryConfig, ForgettingMode
)
from .conversation import Conversation, ConversationContext

if TYPE_CHECKING:
    from dipeo.core.ports import LLMServicePort
    from .conversation_manager import ConversationManager


class Person:
    """LLM agent with memory of a shared global conversation.
    
    Maintains a filtered view of the global conversation managed by
    ConversationManager for inter-person communication.
    """
    
    def __init__(self, id: PersonID, name: str, llm_config: PersonLLMConfig, 
                 conversation_manager: Optional["ConversationManager"] = None):
        self.id = id
        self.name = name
        self.llm_config = llm_config
        self._conversation_manager = conversation_manager
        # For backward compatibility, maintain a local conversation if no manager provided
        self._local_conversation: Optional[Conversation] = Conversation() if not conversation_manager else None
    
    def add_message(self, message: Message) -> None:
        if self._conversation_manager:
            # Add to global conversation via manager
            self._conversation_manager.add_message(
                message=message,
                execution_id=getattr(self._conversation_manager, '_current_execution_id', ''),
                node_id=None
            )
        elif self._local_conversation:
            # Fallback to local conversation for backward compatibility
            self._local_conversation.add_message(message)
    
    def get_context(self) -> ConversationContext:
        conversation = self._get_conversation()
        return conversation.get_context() if conversation else ConversationContext(messages=[], metadata=None, context={})
    
    def get_messages(self) -> List[Message]:
        conversation = self._get_conversation()
        if not conversation:
            return []
        
        # Return messages where this person is involved
        return [
            msg for msg in conversation.messages
            if msg.from_person_id == self.id or msg.to_person_id == self.id
        ]
    
    def get_latest_message(self) -> Optional[Message]:
        messages = self.get_messages()
        return messages[-1] if messages else None
    
    def clear_conversation(self) -> None:
        """Clear this person's memory (backward compatibility only)."""
        if self._conversation_manager:
            # In new architecture, apply forgetting mode to clear person's view
            # This maintains the global conversation but clears this person's memory
            self._conversation_manager.apply_forgetting(
                str(self.id), 
                ForgettingMode.upon_request,
                getattr(self._conversation_manager, '_current_execution_id', None)
            )
        elif self._local_conversation:
            self._local_conversation.clear()
    
    def get_message_count(self) -> int:
        return len(self.get_messages())
    
    def update_context(self, context_updates: Dict[str, Any]) -> None:
        conversation = self._get_conversation()
        if conversation:
            conversation.update_context(context_updates)
    
    def _get_conversation(self) -> Optional[Conversation]:
        if self._conversation_manager:
            # Get global conversation from manager (no person_id needed)
            return self._conversation_manager.get_conversation("")
        return self._local_conversation
    
    @property
    def conversation(self) -> Conversation:
        """Get conversation for backward compatibility."""
        conv = self._get_conversation()
        if not conv:
            raise RuntimeError("No conversation available")
        return conv
    
    async def chat(
        self,
        message: str,
        llm_service: "LLMServicePort",
        from_person_id: Union[PersonID, str] = "system",
        memory_config: Optional[MemoryConfig] = None,
        **llm_options: Any
    ) -> ChatResult:
        """Send message to this person and get LLM response."""
        # Create the incoming message
        incoming = Message(
            from_person_id=from_person_id,  # type: ignore[arg-type]
            to_person_id=self.id,
            content=message,
            message_type="person_to_person" if from_person_id != "system" else "system_to_person"
        )
        self.add_message(incoming)
        
        # Apply forgetting rules if configured
        if memory_config:
            self.forget(memory_config)
        
        # Prepare messages for LLM
        messages = self._prepare_messages_for_llm()
        
        # Call LLM service
        result = await llm_service.complete(
            messages=messages,
            model=self.llm_config.model,
            api_key_id=self.llm_config.api_key_id,
            system_prompt=self.llm_config.system_prompt,
            **llm_options
        )
        
        # Add response to conversation
        # Response goes back to whoever sent the message
        response_message = Message(
            from_person_id=self.id,
            to_person_id=from_person_id,  # type: ignore[arg-type]
            content=result.text,
            message_type="person_to_person" if from_person_id != "system" else "person_to_system",
            token_count=result.token_usage.total if result.token_usage else None
        )
        self.add_message(response_message)
        
        return result
    
    async def complete(
        self,
        prompt: str,
        llm_service: "LLMServicePort",
        **llm_options: Any
    ) -> ChatResult:
        """Complete a prompt using this person's LLM."""
        return await self.chat(
            message=prompt,
            llm_service=llm_service,
            from_person_id=PersonID("system"),
            **llm_options
        )
    
    def forget(self, memory_config: MemoryConfig) -> List[Message]:
        """Apply memory management rules to forget old messages."""
        forgotten = []
        
        if memory_config.forget_mode == ForgettingMode.no_forget:
            # Never forget anything
            return forgotten
        
        if memory_config.forget_mode == ForgettingMode.on_every_turn:
            # For new architecture, delegate to ConversationManager
            if self._conversation_manager:
                count = self._conversation_manager.apply_forgetting(
                    str(self.id), 
                    memory_config.forget_mode,
                    getattr(self._conversation_manager, '_current_execution_id', None)
                )
                # Can't return actual forgotten messages without more info
                return []
            elif self._local_conversation and memory_config.max_messages:
                # Fallback for backward compatibility
                forgotten = self._local_conversation.truncate_to_recent(
                    int(memory_config.max_messages)
                )
        
        # Note: ForgettingMode.upon_request would be handled externally
        # by explicitly calling this method when needed
        
        return forgotten
    
    def _prepare_messages_for_llm(self) -> List[Dict[str, str]]:
        llm_messages = []
        
        # Get messages relevant to this person
        for msg in self.get_messages():
            # Map our message types to LLM roles
            if msg.from_person_id == self.id:
                role = "assistant"
            elif msg.to_person_id == self.id:
                # Messages TO this person are user messages (including from system)
                role = "user"
            else:
                role = "user"
            
            llm_messages.append({
                "role": role,
                "content": msg.content
            })
        
        return llm_messages
    
    def can_see_conversation_of(self, other_person: "Person") -> bool:
        """Check if this person can see another person's conversation."""
        # In new architecture, persons share a global conversation
        # Visibility rules can be configured based on requirements
        return True
    
    def __repr__(self) -> str:
        return (f"Person(id={self.id}, name={self.name}, "
                f"messages={self.get_message_count()}, "
                f"llm={self.llm_config.service}:{self.llm_config.model})")