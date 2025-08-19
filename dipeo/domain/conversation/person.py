"""Person dynamic object representing an LLM agent with evolving conversation state."""

from typing import TYPE_CHECKING, Any

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
    from dipeo.domain.llm.ports import LLMService as LLMServicePort


class Person:
    """LLM agent with filtered view of conversation messages.
    
    This entity manages its own memory filters and view settings,
    but does not directly interact with conversations or repositories.
    """
    
    def __init__(self, id: PersonID, name: str, llm_config: PersonLLMConfig, 
                 memory_view: MemoryView = MemoryView.ALL_INVOLVED):
        self.id = id
        self.name = name
        self.llm_config = llm_config
        
        self.memory_view = memory_view
        self._memory_filter = MemoryFilterFactory.create(memory_view)
        self._memory_limiter: MemoryLimiter | None = None
    
    def filter_messages(self, messages: list[Message], memory_view: MemoryView | None = None) -> list[Message]:
        """Filter messages based on this person's memory view and limits.
        
        Args:
            messages: The full list of messages to filter
            memory_view: Optional override for memory view (uses person's default if None)
            
        Returns:
            Filtered list of messages based on person's perspective
        """
        view = memory_view or self.memory_view
        filter = self._memory_filter if view == self.memory_view else MemoryFilterFactory.create(view)
        
        filtered_messages = filter.filter(messages, self.id)
        if self._memory_limiter:
            filtered_messages = self._memory_limiter.limit(filtered_messages)
        
        return filtered_messages
    
    
    def get_messages(self, all_messages: list[Message], memory_view: MemoryView | None = None) -> list[Message]:
        """Get filtered messages from the provided message list.
        
        Args:
            all_messages: The complete list of messages
            memory_view: Optional override for memory view
            
        Returns:
            Filtered messages based on person's view
        """
        return self.filter_messages(all_messages, memory_view)
    
    
    def get_latest_message(self, all_messages: list[Message]) -> Message | None:
        """Get the latest message from person's filtered view.
        
        Args:
            all_messages: The complete list of messages
            
        Returns:
            The latest message or None if no messages
        """
        messages = self.filter_messages(all_messages)
        return messages[-1] if messages else None
    
    def forget_all_messages(self) -> None:
        """Set memory limit to 0 - person can't see messages but they still exist."""
        self._memory_limiter = MemoryLimiter(0, preserve_system=False)
    
    def reset_memory(self) -> None:
        """Reset memory to forget all messages.
        
        This is used for GOLDFISH memory profile. Instead of clearing messages
        from storage, we just set the memory limit to 0 so the person can't see them.
        """
        self._memory_limiter = MemoryLimiter(0, preserve_system=False)
    
    def get_message_count(self, all_messages: list[Message]) -> int:
        """Get count of messages visible to this person.
        
        Args:
            all_messages: The complete list of messages
            
        Returns:
            Number of messages visible to this person
        """
        return len(self.filter_messages(all_messages))
    
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
        all_messages: list[Message],
        llm_service: "LLMServicePort",
        from_person_id: PersonID | str = "system",
        **llm_options: Any
    ) -> tuple[ChatResult, Message, Message]:
        """Complete prompt with this person's LLM.
        
        This method delegates LLM-specific logic to the infrastructure layer.
        It returns the result and the messages that should be added to the conversation.
        
        Args:
            prompt: The prompt to complete
            all_messages: The complete conversation history
            llm_service: The LLM service to use
            from_person_id: The ID of the person sending the prompt
            **llm_options: Additional options for the LLM
            
        Returns:
            Tuple of (ChatResult, incoming_message, response_message)
        """
        # Create the incoming message
        incoming = Message(
            from_person_id=from_person_id,  # type: ignore[arg-type]
            to_person_id=self.id,
            content=prompt,
            message_type="person_to_person" if from_person_id != "system" else "system_to_person"
        )
        
        # Get messages from this person's filtered view and add the incoming message
        person_messages = self.filter_messages(all_messages)
        person_messages = person_messages + [incoming]
        
        # Delegate to LLM service with person context
        # The infrastructure layer handles system prompts and message formatting
        result = await llm_service.complete_with_person(
            person_messages=person_messages,
            person_id=self.id,
            llm_config=self.llm_config,
            **llm_options
        )
        
        # Create the response message
        response_message = Message(
            from_person_id=self.id,
            to_person_id=from_person_id,  # type: ignore[arg-type]
            content=result.text,
            message_type="person_to_person" if from_person_id != "system" else "person_to_system",
            token_count=result.token_usage.total if result.token_usage else None
        )
        
        return result, incoming, response_message
    
    def get_conversation_context(self, all_messages: list[Message]) -> dict[str, Any]:
        """Get this person's view of the conversation, formatted for templates.
        
        This method respects the person's memory filters and limits,
        providing a consistent view of the conversation that can be used
        in prompts and templates.
        
        Args:
            all_messages: The complete conversation history
        """
        messages = self.filter_messages(all_messages)  # Uses memory filters
        
        # Format messages for template use
        formatted_messages = [
            {
                'from': str(msg.from_person_id) if msg.from_person_id else '',
                'to': str(msg.to_person_id) if msg.to_person_id else '',
                'content': msg.content,
                'type': msg.message_type
            } for msg in messages
        ]
        
        # Build person-specific conversation views
        person_conversations = {}
        for msg in messages:
            # Add to sender's view
            if msg.from_person_id != "system":
                person_id = str(msg.from_person_id)
                if person_id not in person_conversations:
                    person_conversations[person_id] = []
                person_conversations[person_id].append({
                    'role': 'assistant',
                    'content': msg.content
                })
            
            # Add to recipient's view
            if msg.to_person_id != "system":
                person_id = str(msg.to_person_id)
                if person_id not in person_conversations:
                    person_conversations[person_id] = []
                person_conversations[person_id].append({
                    'role': 'user',
                    'content': msg.content
                })
        
        return {
            'global_conversation': formatted_messages,
            'global_message_count': len(messages),
            'person_conversations': person_conversations,
            'last_message': messages[-1].content if messages else None,
            'last_message_from': str(messages[-1].from_person_id) if messages else None,
            'last_message_to': str(messages[-1].to_person_id) if messages else None
        }
    
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
                f"memory_view={self.memory_view.value}, "
                f"llm={self.llm_config.service}:{self.llm_config.model})")