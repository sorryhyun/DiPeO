"""Person dynamic object representing an LLM agent with evolving conversation state."""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dipeo.diagram_generated import (
    ChatResult,
    Message,
    PersonLLMConfig,
    LLMService,
)
from dipeo.diagram_generated.domain_models import PersonID

if TYPE_CHECKING:
    from dipeo.domain.integrations.ports import LLMService as LLMServicePort


class Person:
    """LLM agent with flexible message filtering.
    
    This entity represents an agent but delegates memory filtering
    to external components for maximum flexibility.
    """
    
    def __init__(self, id: PersonID, name: str, llm_config: PersonLLMConfig):
        self.id = id
        self.name = name
        self.llm_config = llm_config
        
        # Brain component - wired up at runtime by executor
        self.brain = None
    
    
    
    def get_messages(self, all_messages: list[Message]) -> list[Message]:
        """Get filtered messages from the provided message list.
        
        Args:
            all_messages: The complete list of messages
            
        Returns:
            Filtered messages based on person's view
        """

        return [
            msg for msg in all_messages
            if msg.from_person_id == self.id or msg.to_person_id == self.id
        ]
    
    def get_latest_message(self, all_messages: list[Message]) -> Message | None:
        """Get the latest message from person's filtered view.
        
        Args:
            all_messages: The complete list of messages
            
        Returns:
            The latest message or None if no messages
        """
        messages = self.get_messages(all_messages)
        return messages[-1] if messages else None
    
    def reset_memory(self) -> None:
        """Reset memory to forget all messages.
        
        This is used for GOLDFISH mode. Brain should handle this.
        """
        # Memory reset is now handled by Brain component
        pass
    
    def get_message_count(self, all_messages: list[Message]) -> int:
        """Get count of messages visible to this person.
        
        Args:
            all_messages: The complete list of messages
            
        Returns:
            Number of messages visible to this person
        """
        return len(self.get_messages(all_messages))
    
    
    def get_memory_config(self) -> dict[str, Any]:
        """Get memory configuration information.
        
        Returns:
            Dictionary with memory configuration details
        """
        return {
            "has_brain": self.brain is not None,
            "description": "Brain-based filtering" if self.brain else "Default ALL_INVOLVED filter",
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
        
        This method handles message formatting and system prompts internally,
        then delegates to the LLM service for the actual completion.
        
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
        
        # Use provided messages directly (already filtered by caller) and add the incoming message
        person_messages = all_messages + [incoming]
        
        # Format messages for LLM consumption
        formatted_messages = self._format_messages_for_llm(person_messages)
        
        # Call LLM service with formatted messages
        result = await llm_service.complete(
            messages=formatted_messages,
            model=self.llm_config.model,
            api_key_id=self.llm_config.api_key_id,
            service=self.llm_config.service,
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
    
    def _format_messages_for_llm(self, messages: list[Message]) -> list[dict[str, str]]:
        """Format domain messages for LLM consumption.
        
        Args:
            messages: List of domain Message objects
            
        Returns:
            List of formatted message dictionaries with "role" and "content" keys
        """
        llm_messages = []
        
        # Add system prompt if configured
        system_prompt = self._get_system_prompt()
        if system_prompt:
            # Determine system role based on service
            system_role = "developer" if self.llm_config.service == LLMService.OPENAI else "system"
            llm_messages.append({
                "role": system_role,
                "content": system_prompt
            })
        
        # Convert domain messages to LLM format
        for msg in messages:
            role = self._determine_message_role(msg)
            llm_messages.append({
                "role": role,
                "content": msg.content
            })
        
        return llm_messages
    
    def _determine_message_role(self, message: Message) -> str:
        """Determine the LLM role for a message.
        
        Args:
            message: The domain message
            
        Returns:
            The role string ("user" or "assistant")
        """
        # If the message is from this person, they are the assistant
        if message.from_person_id == self.id:
            return "assistant"
        # If the message is to this person, the sender is the user
        elif message.to_person_id == self.id:
            return "user"
        # Default to user for other cases
        else:
            return "user"
    
    def _get_system_prompt(self) -> Optional[str]:
        """Get the system prompt from configuration.
        
        Follows priority:
        1. prompt_file if specified and exists
        2. system_prompt if directly configured
        
        Returns:
            The system prompt content, or None if not configured
        """
        # Check if prompt_file is specified
        if self.llm_config.prompt_file:
            prompt_content = self._load_prompt_from_file(self.llm_config.prompt_file)
            if prompt_content is not None:
                return prompt_content
        
        # Use system_prompt if available
        return self.llm_config.system_prompt
    
    def _load_prompt_from_file(self, prompt_file: str) -> Optional[str]:
        """Load prompt content from a file.
        
        Args:
            prompt_file: Path to the prompt file
            
        Returns:
            The file content, or None if file cannot be read
        """
        # Resolve path relative to DIPEO_BASE_DIR if not absolute
        prompt_path = Path(prompt_file)
        if not prompt_path.is_absolute():
            base_dir = os.environ.get('DIPEO_BASE_DIR', os.getcwd())
            prompt_path = Path(base_dir) / prompt_path
        
        # Read prompt from file if it exists
        if prompt_path.exists():
            try:
                return prompt_path.read_text(encoding='utf-8')
            except Exception:
                return None
        return None
    
    def get_conversation_context(self, all_messages: list[Message]) -> dict[str, Any]:
        """Get this person's view of the conversation, formatted for templates.
        
        This method respects the person's memory filters and limits,
        providing a consistent view of the conversation that can be used
        in prompts and templates.
        
        Args:
            all_messages: The complete conversation history
        """
        messages = self.get_messages(all_messages)  # Uses memory filters
        
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


    
    
    async def select_memories(
        self,
        candidate_messages: list[Message],
        prompt_preview: str,
        memorize_to: Optional[str],
        at_most: Optional[int],
        llm_service=None,
        **kwargs
    ) -> Optional[list[Message]]:
        """Select relevant memories using brain's cognitive capabilities.
        
        Delegates to brain if available, providing a clean API at the Person level.
        
        Args:
            candidate_messages: Messages to select from
            prompt_preview: Preview of the upcoming task
            memorize_to: Selection criteria
            at_most: Maximum messages to select
            llm_service: LLM service for intelligent selection
            **kwargs: Additional parameters for the brain
            
        Returns:
            Selected messages or None if brain not available
        """
        if self.brain:
            return await self.brain.select_memories(
                person=self,
                candidate_messages=candidate_messages,
                prompt_preview=prompt_preview,
                memorize_to=memorize_to,
                at_most=at_most,
                llm_service=llm_service,
                **kwargs
            )
        return None
    
    def score_message(
        self,
        message: Message,
        frequency_count: int = 1,
        current_time: Optional[Any] = None
    ) -> float:
        """Score a message based on various factors.
        
        Delegates to brain if available.
        
        Args:
            message: The message to score
            frequency_count: How many similar messages exist
            current_time: Current time for recency calculation
            
        Returns:
            Float score between 0-100, or 0 if brain not available
        """
        if self.brain:
            return self.brain.score_message(
                message,
                frequency_count=frequency_count,
                current_time=current_time
            )
        return 0.0
    
    async def complete_with_memory(
        self,
        prompt: str,
        all_messages: list[Message],
        llm_service: "LLMServicePort",
        from_person_id: PersonID | str = "system",
        memorize_to: Optional[str] = None,
        at_most: Optional[int] = None,
        prompt_preview: Optional[str] = None,
        **llm_options: Any
    ) -> tuple[ChatResult, Message, Message, Optional[list[Message]]]:
        """Complete prompt with intelligent memory selection.
        
        This method consolidates memory selection and completion into a single call,
        using the brain's cognitive capabilities to filter messages before completion.
        
        Args:
            prompt: The prompt to complete
            all_messages: The complete conversation history
            llm_service: The LLM service to use
            from_person_id: The ID of the person sending the prompt
            memorize_to: Optional memory selection criteria (e.g., "recent", "important", "GOLDFISH")
            at_most: Optional maximum number of messages to select
            prompt_preview: Optional preview of the task for better memory selection
            **llm_options: Additional options for the LLM
            
        Returns:
            Tuple of (ChatResult, incoming_message, response_message, selected_messages)
            The selected_messages can be None if no selection criteria was provided
        """
        # Determine which messages to use for completion
        selected_messages = None
        messages_for_completion = all_messages
        
        # Apply memory selection if criteria provided
        if memorize_to and self.brain:
            # Use prompt_preview if provided, otherwise use the actual prompt
            preview = prompt_preview or prompt
            
            # Perform memory selection through brain
            selected_messages = await self.brain.select_memories(
                person=self,
                candidate_messages=all_messages,
                prompt_preview=preview,
                memorize_to=memorize_to,
                at_most=at_most,
                llm_service=llm_service
            )
            
            # Use selected messages if selection was performed
            if selected_messages is not None:
                messages_for_completion = selected_messages
            else:
                # Fallback to default filtering if brain couldn't select
                messages_for_completion = self.get_messages(all_messages)
        else:
            # No memory criteria - use default person filtering
            messages_for_completion = self.get_messages(all_messages)
        
        # Now complete with the filtered messages
        result, incoming, response = await self.complete(
            prompt=prompt,
            all_messages=messages_for_completion,
            llm_service=llm_service,
            from_person_id=from_person_id,
            **llm_options
        )
        
        # Return everything including the selected messages for transparency
        return result, incoming, response, selected_messages

    
    def __repr__(self) -> str:
        brain_info = "with_brain" if self.brain else "no_brain"
        hand_info = "with_hand" if self.hand else "no_hand"
        return (f"Person(id={self.id}, name={self.name}, "
                f"{brain_info}, {hand_info}, "
                f"llm={self.llm_config.service}:{self.llm_config.model})")