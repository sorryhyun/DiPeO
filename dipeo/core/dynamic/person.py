"""Person dynamic object representing an LLM agent with evolving conversation state."""

from typing import TYPE_CHECKING, Any, Optional

from dipeo.models import (
    ChatResult,
    MemorySettings,
    MemoryView as MemoryViewEnum,
    Message,
    PersonID,
    PersonLLMConfig,
)

from .conversation import Conversation, ConversationContext
from .memory_filters import MemoryFilterFactory, MemoryLimiter, MemoryView

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
        
        self.memory_view = memory_view
        self._memory_filter = MemoryFilterFactory.create(memory_view)
        self._memory_limiter: MemoryLimiter | None = None
    
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
    
    def get_messages(self, memory_view: MemoryView | None = None) -> list[Message]:
        if not self._conversation_manager:
            return []
        
        conversation = self._conversation_manager.get_conversation()
        
        view = memory_view or self.memory_view
        filter = self._memory_filter if view == self.memory_view else MemoryFilterFactory.create(view)
        
        filtered_messages = filter.filter(conversation.messages, self.id)
        if self._memory_limiter:
            filtered_messages = self._memory_limiter.limit(filtered_messages)
        
        return filtered_messages
    
    
    def get_latest_message(self) -> Message | None:
        messages = self.get_messages()
        return messages[-1] if messages else None
    
    def forget_all_messages(self) -> None:
        """Apply extreme forgetting by setting memory limit to 0.
        
        Note: In the global conversation model, this doesn't delete messages
        but makes the person unable to see any messages.
        """
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
    
    def get_memory_config(self) -> dict[str, Any]:
        """Get current memory configuration."""
        return {
            "view": self.memory_view.value,
            "filter_description": self._memory_filter.describe(),
            "max_messages": self._memory_limiter.max_messages if self._memory_limiter else None,
            "preserve_system": self._memory_limiter.preserve_system if self._memory_limiter else None
        }
    
    def update_context(self, context_updates: dict[str, Any]) -> None:
        if self._conversation_manager:
            conversation = self._conversation_manager.get_conversation()
            conversation.update_context(context_updates)
    
    def _get_conversation(self) -> Conversation | None:
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
        from_person_id: PersonID | str = "system",
        **llm_options: Any
    ) -> ChatResult:
        """Complete a prompt using this person's LLM.
        
        Note: Memory settings should be applied before calling this method,
        typically by the handler at the appropriate time.
        """
        # Create the incoming message
        incoming = Message(
            from_person_id=from_person_id,  # type: ignore[arg-type]
            to_person_id=self.id,
            content=prompt,
            message_type="person_to_person" if from_person_id != "system" else "system_to_person"
        )
        self.add_message(incoming)
        
        # Prepare messages for LLM
        messages = self._prepare_messages_for_llm()
        
        # Call LLM service
        result = await llm_service.complete(
            messages=messages,
            model=self.llm_config.model,
            api_key_id=self.llm_config.api_key_id,
            **llm_options
        )
        
        response_message = Message(
            from_person_id=self.id,
            to_person_id=from_person_id,  # type: ignore[arg-type]
            content=result.text,
            message_type="person_to_person" if from_person_id != "system" else "person_to_system",
            token_count=result.token_usage.total if result.token_usage else None
        )
        self.add_message(response_message)
        
        return result
    
    def apply_memory_settings(self, settings: MemorySettings) -> None:
        """Apply unified memory settings - view and limit.
        
        This is the main method for configuring person memory.
        It replaces the complex forgetting strategies with a simple view + limit approach.
        """
        view_mapping = {
            MemoryViewEnum.ALL_INVOLVED: MemoryView.ALL_INVOLVED,
            MemoryViewEnum.SENT_BY_ME: MemoryView.SENT_BY_ME,
            MemoryViewEnum.SENT_TO_ME: MemoryView.SENT_TO_ME,
            MemoryViewEnum.SYSTEM_AND_ME: MemoryView.SYSTEM_AND_ME,
            MemoryViewEnum.CONVERSATION_PAIRS: MemoryView.CONVERSATION_PAIRS,
        }
        
        memory_view = view_mapping.get(settings.view, MemoryView.ALL_INVOLVED)
        self.set_memory_view(memory_view)
        
        if settings.max_messages and settings.max_messages > 0:
            self.set_memory_limit(
                int(settings.max_messages), 
                preserve_system=settings.preserve_system if settings.preserve_system is not None else True
            )
        else:
            self._memory_limiter = None
    
    
    def _prepare_messages_for_llm(self) -> list[dict[str, str]]:
        llm_messages = []
        
        if self.llm_config.system_prompt:
            llm_messages.append({
                "role": "system",
                "content": self.llm_config.system_prompt
            })
        
        for msg in self.get_messages():
            if msg.from_person_id == self.id:
                role = "assistant"
            elif msg.to_person_id == self.id:
                role = "user"
            else:
                role = "user"
            
            llm_messages.append({
                "role": role,
                "content": msg.content
            })
        
        return llm_messages
    
    
    def __repr__(self) -> str:
        return (f"Person(id={self.id}, name={self.name}, "
                f"messages={self.get_message_count()}, "
                f"llm={self.llm_config.service}:{self.llm_config.model})")