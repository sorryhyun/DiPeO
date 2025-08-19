"""Message formatting for LLM services."""

from typing import Optional
import logging

from dipeo.diagram_generated import Message, LLMService, PersonLLMConfig
from dipeo.diagram_generated.domain_models import PersonID
from .system_prompt_handler import SystemPromptHandler
logger = logging.getLogger(__name__)


class MessageFormatter:
    """Formats messages for different LLM providers.
    
    This class handles the conversion of domain messages to provider-specific
    formats, including proper role mapping and message structure.
    """
    
    def format_messages_for_llm(
        self,
        messages: list[Message],
        person_id: PersonID,
        system_prompt: Optional[str] = None,
        service: LLMService = LLMService.OPENAI,
        system_role: str = "system"
    ) -> list[dict[str, str]]:
        """Format domain messages for LLM consumption.
        
        Args:
            messages: List of domain Message objects
            person_id: The ID of the person (assistant) in the conversation
            system_prompt: Optional system prompt to prepend
            service: The LLM service being used
            system_role: The role name for system messages (e.g., "developer" for OpenAI)
            
        Returns:
            List of formatted message dictionaries with "role" and "content" keys
        """
        llm_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            llm_messages.append({
                "role": system_role,
                "content": system_prompt
            })
        
        # Convert domain messages to LLM format
        for msg in messages:
            role = self._determine_message_role(msg, person_id)
            llm_messages.append({
                "role": role,
                "content": msg.content
            })
        
        return llm_messages
    
    def _determine_message_role(self, message: Message, person_id: PersonID) -> str:
        """Determine the LLM role for a message.
        
        Args:
            message: The domain message
            person_id: The ID of the person (assistant)
            
        Returns:
            The role string ("user" or "assistant")
        """
        # If the message is from the person, they are the assistant
        if message.from_person_id == person_id:
            return "assistant"
        # If the message is to the person, the sender is the user
        elif message.to_person_id == person_id:
            return "user"
        # Default to user for other cases (e.g., system messages)
        else:
            return "user"
    
    def prepare_llm_messages(
        self,
        person_messages: list[Message],
        person_id: PersonID,
        llm_config: PersonLLMConfig,
        system_prompt_handler: 'SystemPromptHandler'
    ) -> list[dict[str, str]]:
        """Prepare complete message list for LLM, including system prompt.
        
        This is a convenience method that combines system prompt handling
        with message formatting.
        
        Args:
            person_messages: List of messages from the person's view
            person_id: The person's ID
            llm_config: The person's LLM configuration
            system_prompt_handler: Handler for resolving system prompts
            
        Returns:
            Complete list of formatted messages ready for LLM
        """
        # Get system prompt from configuration
        system_prompt = system_prompt_handler.get_system_prompt(llm_config)
        
        # Get appropriate system role for the service
        system_role = system_prompt_handler.get_system_role(llm_config.service)
        
        # Format messages with system prompt
        return self.format_messages_for_llm(
            messages=person_messages,
            person_id=person_id,
            system_prompt=system_prompt,
            service=llm_config.service,
            system_role=system_role
        )