"""Person dynamic object representing an LLM agent with evolving conversation state."""

from typing import TYPE_CHECKING, Any, Optional

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
        
        # Brain and Hand components - wired up at runtime by executor
        self.brain = None
        self.hand = None
    
    
    
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
        person_messages = self.get_messages(all_messages)
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

    
    async def complete_with_hand(
        self,
        messages: Optional[list[Message]] = None,
        execution_id: str = "",
        node_id: str = "",
        prompt: Optional[str] = None,
        llm_service=None,
        **kwargs: Any
    ) -> Any:
        """Execute LLM completion using the hand component.
        
        Delegates to hand if available for clean execution API.
        
        Args:
            messages: Optional messages to use
            execution_id: Unique execution identifier
            node_id: Node identifier
            prompt: The prompt to execute
            llm_service: LLM service to use
            **kwargs: Additional parameters
            
        Returns:
            ChatResult from the completion or None if hand not available
        """
        if self.hand:
            return await self.hand.complete_with_messages(
                person=self,
                messages=messages,
                execution_id=execution_id,
                node_id=node_id,
                prompt=prompt,
                llm_service=llm_service,
                **kwargs
            )
        return None
    
    def __repr__(self) -> str:
        brain_info = "with_brain" if self.brain else "no_brain"
        hand_info = "with_hand" if self.hand else "no_hand"
        return (f"Person(id={self.id}, name={self.name}, "
                f"{brain_info}, {hand_info}, "
                f"llm={self.llm_config.service}:{self.llm_config.model})")