"""Person dynamic object representing an LLM agent with evolving conversation state."""

from typing import Dict, Any, List, Optional, TYPE_CHECKING, Union

from dipeo.models import (
    PersonLLMConfig, Message, PersonID, ChatResult, 
    MemoryConfig, ForgettingMode
)
from .conversation import Conversation, ConversationContext

if TYPE_CHECKING:
    from dipeo.core.ports import LLMServicePort


class Person:
    """Represents an LLM agent with evolving conversation state.
    
    This is a dynamic object that maintains and manages conversation history
    and context during diagram execution. Each person has their own independent
    conversation state that evolves as messages are exchanged.
    """
    
    def __init__(self, id: PersonID, name: str, llm_config: PersonLLMConfig):
        """Initialize a Person with configuration and empty conversation.
        
        Args:
            id: Unique identifier for this person
            name: Display name for this person
            llm_config: LLM configuration including service, model, and settings
        """
        self.id = id
        self.name = name
        self.llm_config = llm_config
        self.conversation: Conversation = Conversation()
    
    def add_message(self, message: Message) -> None:
        """Add a message to this person's conversation history.
        
        Args:
            message: The message to add to the conversation
        """
        self.conversation.add_message(message)
    
    def get_context(self) -> ConversationContext:
        """Get the current conversation context for this person.
        
        Returns:
            ConversationContext containing messages and metadata
        """
        return self.conversation.get_context()
    
    def get_messages(self) -> List[Message]:
        """Get all messages in this person's conversation.
        
        Returns:
            List of messages in chronological order
        """
        return self.conversation.messages
    
    def get_latest_message(self) -> Optional[Message]:
        """Get the most recent message in the conversation.
        
        Returns:
            The latest message or None if conversation is empty
        """
        return self.conversation.get_latest_message()
    
    def clear_conversation(self) -> None:
        """Clear all messages from this person's conversation."""
        self.conversation.clear()
    
    def get_message_count(self) -> int:
        """Get the number of messages in this person's conversation.
        
        Returns:
            Total number of messages
        """
        return len(self.conversation.messages)
    
    def update_context(self, context_updates: Dict[str, Any]) -> None:
        """Update the conversation context with new values.
        
        Args:
            context_updates: Dictionary of context values to merge
        """
        self.conversation.update_context(context_updates)
    
    async def chat(
        self,
        message: str,
        llm_service: "LLMServicePort",
        from_person_id: Union[PersonID, str] = "system",
        memory_config: Optional[MemoryConfig] = None,
        **llm_options: Any
    ) -> ChatResult:
        """Have a conversation with this person using their LLM.
        
        This method:
        1. Adds the incoming message to the conversation
        2. Applies memory management if configured
        3. Calls the LLM to generate a response
        4. Adds the response to the conversation
        5. Returns the LLM result
        
        Args:
            message: The message content to send to this person
            llm_service: The LLM service port to use for completion
            from_person_id: ID of the person sending the message (default: "system")
            memory_config: Optional memory configuration for this interaction
            **llm_options: Additional LLM-specific options (temperature, max_tokens, etc.)
            
        Returns:
            ChatResult containing the response and token usage
        """
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
        """Complete a prompt using this person's LLM (alias for chat).
        
        This is a convenience method that calls chat() with default parameters.
        
        Args:
            prompt: The prompt to complete
            llm_service: The LLM service port to use for completion
            **llm_options: Additional LLM-specific options
            
        Returns:
            ChatResult containing the completion
        """
        return await self.chat(
            message=prompt,
            llm_service=llm_service,
            from_person_id=PersonID("system"),
            **llm_options
        )
    
    def forget(self, memory_config: MemoryConfig) -> List[Message]:
        """Apply memory management rules to forget old messages.
        
        This method respects the forgetting mode and max_messages settings
        to manage the conversation history size.
        
        Args:
            memory_config: Configuration for memory management
            
        Returns:
            List of messages that were forgotten/removed
        """
        forgotten = []
        
        if memory_config.forget_mode == ForgettingMode.no_forget:
            # Never forget anything
            return forgotten
        
        if memory_config.forget_mode == ForgettingMode.on_every_turn:
            # Keep only the most recent messages based on max_messages
            if memory_config.max_messages:
                forgotten = self.conversation.truncate_to_recent(
                    int(memory_config.max_messages)
                )
        
        # Note: ForgettingMode.upon_request would be handled externally
        # by explicitly calling this method when needed
        
        return forgotten
    
    def _prepare_messages_for_llm(self) -> List[Dict[str, str]]:
        """Convert conversation messages to LLM-compatible format.
        
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        llm_messages = []
        
        for msg in self.conversation.messages:
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
    def can_see_conversation_of(other_person: "Person") -> bool:  # pylint: disable=unused-argument
        """Check if this person can see another person's conversation.
        
        By default, persons cannot see each other's conversations.
        This ensures proper isolation between different agents.
        
        Args:
            other_person: The other person to check
            
        Returns:
            False - persons have isolated conversations
        """
        return False
    
    def __repr__(self) -> str:
        """String representation of the Person."""
        return (f"Person(id={self.id}, name={self.name}, "
                f"messages={self.get_message_count()}, "
                f"llm={self.llm_config.service}:{self.llm_config.model})")