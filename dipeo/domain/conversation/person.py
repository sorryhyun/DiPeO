"""Person dynamic object representing an LLM agent with evolving conversation state."""

from typing import TYPE_CHECKING, Any, Optional, Callable

from dipeo.diagram_generated import (
    ChatResult,
    Message,
    PersonLLMConfig,
)
from dipeo.diagram_generated.domain_models import PersonID

if TYPE_CHECKING:
    from dipeo.domain.llm.ports import LLMService as LLMServicePort


class Person:
    """LLM agent with flexible message filtering.
    
    This entity represents an agent but delegates memory filtering
    to external components for maximum flexibility.
    """
    
    def __init__(self, id: PersonID, name: str, llm_config: PersonLLMConfig):
        self.id = id
        self.name = name
        self.llm_config = llm_config
        
        # Simple default filter function - can be overridden
        self._filter_func: Optional[Callable[[list[Message]], list[Message]]] = None
    
    def filter_messages(self, messages: list[Message]) -> list[Message]:
        """Filter messages using configured filter function.
        
        Args:
            messages: The full list of messages to filter
            
        Returns:
            Filtered list of messages (defaults to ALL_INVOLVED behavior)
        """
        if self._filter_func:
            return self._filter_func(messages)
        
        # Default behavior: ALL_INVOLVED (messages where person is sender or recipient)
        return [
            msg for msg in messages
            if msg.from_person_id == self.id or msg.to_person_id == self.id
        ]
    
    
    def get_messages(self, all_messages: list[Message]) -> list[Message]:
        """Get filtered messages from the provided message list.
        
        Args:
            all_messages: The complete list of messages
            
        Returns:
            Filtered messages based on person's view
        """
        return self.filter_messages(all_messages)
    
    
    def get_latest_message(self, all_messages: list[Message]) -> Message | None:
        """Get the latest message from person's filtered view.
        
        Args:
            all_messages: The complete list of messages
            
        Returns:
            The latest message or None if no messages
        """
        messages = self.filter_messages(all_messages)
        return messages[-1] if messages else None
    
    def reset_memory(self) -> None:
        """Reset memory to forget all messages.
        
        This is used for GOLDFISH mode. Sets filter to return empty list.
        """
        self._filter_func = lambda messages: []
    
    def get_message_count(self, all_messages: list[Message]) -> int:
        """Get count of messages visible to this person.
        
        Args:
            all_messages: The complete list of messages
            
        Returns:
            Number of messages visible to this person
        """
        return len(self.filter_messages(all_messages))
    
    def set_filter_function(self, filter_func: Optional[Callable[[list[Message]], list[Message]]]) -> None:
        """Set a custom filter function for this person.
        
        Args:
            filter_func: Function that takes messages and returns filtered messages
        """
        self._filter_func = filter_func
    
    def get_memory_config(self) -> dict[str, Any]:
        """Get memory configuration information.
        
        Returns:
            Dictionary with memory configuration details
        """
        return {
            "has_custom_filter": self._filter_func is not None,
            "description": "Custom filter applied" if self._filter_func else "Default ALL_INVOLVED filter",
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


    
    
    def __repr__(self) -> str:
        filter_info = "custom_filter" if self._filter_func else "default_filter"
        return (f"Person(id={self.id}, name={self.name}, "
                f"filter={filter_info}, "
                f"llm={self.llm_config.service}:{self.llm_config.model})")