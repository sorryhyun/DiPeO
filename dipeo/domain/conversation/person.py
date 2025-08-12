"""Person dynamic object representing an LLM agent with evolving conversation state."""

from typing import TYPE_CHECKING, Any, Optional

from dipeo.diagram_generated import (
    ChatResult,
    MemorySettings,
    Message,
    PersonLLMConfig,
)
from dipeo.diagram_generated import (
    MemoryView as MemoryViewEnum,
)
from dipeo.diagram_generated.domain_models import PersonID

from .memory_filters import MemoryFilterFactory, MemoryLimiter, MemoryView

if TYPE_CHECKING:
    from dipeo.core.ports import LLMServicePort

    from .conversation_manager import ConversationManager


class Person:
    """LLM agent with filtered view of global conversation."""
    
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
        """Set memory limit to 0 - person can't see messages but they still exist."""
        self._memory_limiter = MemoryLimiter(0, preserve_system=False)
    
    def get_message_count(self) -> int:
        return len(self.get_messages())
    
    def set_memory_view(self, view: MemoryView) -> None:
        self.memory_view = view
        self._memory_filter = MemoryFilterFactory.create(view)
    
    def set_memory_limit(self, max_messages: int, preserve_system: bool = True) -> None:
        if max_messages <= 0:
            self._memory_limiter = None
        else:
            self._memory_limiter = MemoryLimiter(max_messages, preserve_system)
    
    def get_memory_config(self) -> dict[str, Any]:
        return {
            "view": self.memory_view.value,
            "filter_description": self._memory_filter.describe(),
            "max_messages": self._memory_limiter.max_messages if self._memory_limiter else None,
            "preserve_system": self._memory_limiter.preserve_system if self._memory_limiter else None
        }
    
    
    async def complete(
        self,
        prompt: str,
        llm_service: "LLMServicePort",
        from_person_id: PersonID | str = "system",
        **llm_options: Any
    ) -> ChatResult:
        """Complete prompt with this person's LLM.
        
        This method now delegates all LLM-specific logic to the infrastructure layer.
        The Person class only manages conversation state and memory.
        """
        # Create the incoming message
        incoming = Message(
            from_person_id=from_person_id,  # type: ignore[arg-type]
            to_person_id=self.id,
            content=prompt,
            message_type="person_to_person" if from_person_id != "system" else "system_to_person"
        )
        self.add_message(incoming)
        
        # Get messages from this person's filtered view
        person_messages = self.get_messages()
        
        # Delegate to LLM service with person context
        # The infrastructure layer handles system prompts and message formatting
        result = await llm_service.complete_with_person(
            person_messages=person_messages,
            person_id=self.id,
            llm_config=self.llm_config,
            **llm_options
        )
        
        # Record the response message
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
        """Apply memory settings - main method for person memory configuration."""
        view_mapping = {
            MemoryViewEnum.ALL_INVOLVED: MemoryView.ALL_INVOLVED,
            MemoryViewEnum.SENT_BY_ME: MemoryView.SENT_BY_ME,
            MemoryViewEnum.SENT_TO_ME: MemoryView.SENT_TO_ME,
            MemoryViewEnum.SYSTEM_AND_ME: MemoryView.SYSTEM_AND_ME,
            MemoryViewEnum.CONVERSATION_PAIRS: MemoryView.CONVERSATION_PAIRS,
        }
        
        memory_view = view_mapping.get(settings.view, MemoryView.ALL_INVOLVED)
        self.set_memory_view(memory_view)
        
        if settings.max_messages is not None and settings.max_messages > 0:
            self.set_memory_limit(
                int(settings.max_messages), 
                preserve_system=settings.preserve_system if settings.preserve_system is not None else True
            )
        else:
            self._memory_limiter = None
    
    
    def __repr__(self) -> str:
        return (f"Person(id={self.id}, name={self.name}, "
                f"messages={self.get_message_count()}, "
                f"llm={self.llm_config.service}:{self.llm_config.model})")