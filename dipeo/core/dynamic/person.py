"""Person dynamic object representing an LLM agent with evolving conversation state."""

from typing import Dict, Any, List, Optional, TYPE_CHECKING, Union

from dipeo.models import (
    PersonLLMConfig, Message, PersonID, ChatResult, 
    MemoryConfig, ForgettingMode
)
from .conversation import Conversation, ConversationContext
from .memory_filters import MemoryView, MemoryFilterFactory, MemoryLimiter

if TYPE_CHECKING:
    from dipeo.core.ports import LLMServicePort
    from .conversation_manager import ConversationManager


class Person:
    """LLM agent with memory of a shared global conversation.
    
    Maintains a filtered view of the global conversation managed by
    ConversationManager for inter-person communication.
    """
    
    def __init__(self, id: PersonID, name: str, llm_config: PersonLLMConfig, 
                 conversation_manager: Optional["ConversationManager"] = None,
                 memory_view: MemoryView = MemoryView.ALL_INVOLVED):
        self.id = id
        self.name = name
        self.llm_config = llm_config
        self._conversation_manager = conversation_manager
        
        # Memory management
        self.memory_view = memory_view
        self._memory_filter = MemoryFilterFactory.create(memory_view)
        self._memory_limiter: Optional[MemoryLimiter] = None
    
    def add_message(self, message: Message) -> None:
        if not self._conversation_manager:
            raise RuntimeError("Person requires ConversationManager for message handling")
        
        self._conversation_manager.add_message(
            message=message,
            execution_id=getattr(self._conversation_manager, '_current_execution_id', ''),
            node_id=None
        )
    
    def get_context(self) -> ConversationContext:
        if not self._conversation_manager:
            return ConversationContext(messages=[], metadata=None, context={})
        
        conversation = self._conversation_manager.get_conversation()
        return conversation.get_context()
    
    def get_messages(self, memory_view: Optional[MemoryView] = None) -> List[Message]:
        if not self._conversation_manager:
            return []
        
        conversation = self._conversation_manager.get_conversation()
        
        # Use specified view or default view
        view = memory_view or self.memory_view
        filter = self._memory_filter if view == self.memory_view else MemoryFilterFactory.create(view)
        
        # Apply memory filter
        filtered_messages = filter.filter(conversation.messages, self.id)
        
        # Apply memory limit if configured
        if self._memory_limiter:
            filtered_messages = self._memory_limiter.limit(filtered_messages)
        
        return filtered_messages
    
    def get_latest_message(self) -> Optional[Message]:
        messages = self.get_messages()
        return messages[-1] if messages else None
    
    def clear_conversation(self) -> None:
        """Clear this person's memory view.
        
        Note: In the global conversation model, this doesn't delete messages
        but can reset the person's memory filters or limits.
        """
        # Reset memory limiter to effectively "forget" messages
        self._memory_limiter = MemoryLimiter(0, preserve_system=False)
    
    def get_message_count(self) -> int:
        return len(self.get_messages())
    
    def set_memory_view(self, view: MemoryView) -> None:
        """Change the default memory view for this person."""
        self.memory_view = view
        self._memory_filter = MemoryFilterFactory.create(view)
    
    def set_memory_limit(self, max_messages: int, preserve_system: bool = True) -> None:
        """Set a memory limit for this person's view of the conversation."""
        if max_messages <= 0:
            self._memory_limiter = None
        else:
            self._memory_limiter = MemoryLimiter(max_messages, preserve_system)
    
    def get_memory_config(self) -> Dict[str, Any]:
        """Get current memory configuration."""
        return {
            "view": self.memory_view.value,
            "filter_description": self._memory_filter.describe(),
            "max_messages": self._memory_limiter.max_messages if self._memory_limiter else None,
            "preserve_system": self._memory_limiter.preserve_system if self._memory_limiter else None
        }
    
    def update_context(self, context_updates: Dict[str, Any]) -> None:
        if self._conversation_manager:
            conversation = self._conversation_manager.get_conversation()
            conversation.update_context(context_updates)
    
    def _get_conversation(self) -> Optional[Conversation]:
        if not self._conversation_manager:
            return None
        return self._conversation_manager.get_conversation()
    
    @property
    def conversation(self) -> Conversation:
        """Get the global conversation."""
        conv = self._get_conversation()
        if not conv:
            raise RuntimeError("No conversation available")
        return conv
    
    async def complete(
        self,
        prompt: str,
        llm_service: "LLMServicePort",
        from_person_id: Union[PersonID, str] = "system",
        memory_config: Optional[MemoryConfig] = None,
        **llm_options: Any
    ) -> ChatResult:
        """Complete a prompt using this person's LLM."""
        # Create the incoming message
        incoming = Message(
            from_person_id=from_person_id,  # type: ignore[arg-type]
            to_person_id=self.id,
            content=prompt,
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
    
    def apply_memory_management(self, memory_config: MemoryConfig) -> int:
        """Apply memory management rules including forgetting and limits.
        
        Returns:
            Number of messages affected by memory management
        """
        affected_count = 0
        
        # Apply memory limit if specified
        if memory_config.max_messages and memory_config.max_messages > 0:
            self.set_memory_limit(int(memory_config.max_messages))
        
        # Apply forgetting mode
        if memory_config.forget_mode == ForgettingMode.no_forget:
            return 0
        
        if self._conversation_manager:
            # Delegate to ConversationManager
            affected_count = self._conversation_manager.apply_forgetting(
                str(self.id), 
                memory_config.forget_mode,
                getattr(self._conversation_manager, '_current_execution_id', None)
            )
        else:
            # Without conversation manager, apply forgetting through memory limits
            if memory_config.forget_mode == ForgettingMode.on_every_turn:
                # Keep only last message by setting very restrictive memory limit
                self.set_memory_limit(1, preserve_system=True)
                affected_count = 1  # Approximate
            
            elif memory_config.forget_mode == ForgettingMode.upon_request:
                # Clear all messages by setting limit to 0
                self.set_memory_limit(0, preserve_system=False)
                affected_count = 1  # Approximate
        
        return affected_count
    
    def forget(self, memory_config: MemoryConfig) -> int:
        """Apply memory management rules to forget old messages.
        
        Returns:
            Number of messages affected by memory management
        """
        return self.apply_memory_management(memory_config)
    
    def _prepare_messages_for_llm(self) -> List[Dict[str, str]]:
        llm_messages = []
        
        # Add system prompt as first message if present
        if self.llm_config.system_prompt:
            llm_messages.append({
                "role": "system",
                "content": self.llm_config.system_prompt
            })
        
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
    
    @staticmethod
    def can_see_conversation_of(other_person: "Person") -> bool:
        """Check if this person can see another person's conversation."""
        # In new architecture, persons share a global conversation
        # Visibility rules can be configured based on requirements
        return True
    
    def __repr__(self) -> str:
        return (f"Person(id={self.id}, name={self.name}, "
                f"messages={self.get_message_count()}, "
                f"llm={self.llm_config.service}:{self.llm_config.model})")