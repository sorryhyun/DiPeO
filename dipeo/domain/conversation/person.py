"""Person dynamic object representing an LLM agent with evolving conversation state."""

from typing import TYPE_CHECKING, Any, Optional

from dipeo.diagram_generated import (
    ChatResult,
    LLMService,
    Message,
    PersonLLMConfig,
)
from dipeo.diagram_generated.domain_models import PersonID

if TYPE_CHECKING:
    from dipeo.domain.conversation.memory_strategies import MemorySelectionStrategy
    from dipeo.domain.integrations.ports import LLMService as LLMServicePort


class Person:
    """LLM agent with integrated memory selection strategies.

    This refactored version integrates memory selection directly into Person,
    using a strategy pattern instead of a separate Brain component.
    """

    def __init__(
        self,
        id: PersonID,
        name: str,
        llm_config: PersonLLMConfig,
        memory_strategy: Optional["MemorySelectionStrategy"] = None,
    ):
        self.id = id
        self.name = name
        self.llm_config = llm_config

        # Memory selection strategy (optional)
        self._memory_strategy = memory_strategy

    def get_memory_config(self) -> dict[str, Any]:
        """Get memory configuration information.

        Returns:
            Dictionary with memory configuration details
        """
        return {
            "has_strategy": self._memory_strategy is not None,
            "description": (
                "Strategy-based memory selection"
                if self._memory_strategy
                else "No memory filtering"
            ),
        }

    async def complete(
        self,
        prompt: str,
        all_messages: list[Message],
        llm_service: "LLMServicePort",
        from_person_id: PersonID | str = "system",
        **llm_options: Any,
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
            message_type="person_to_person" if from_person_id != "system" else "system_to_person",
        )

        # Use provided messages directly (already filtered by caller) and add the incoming message
        person_messages = [*all_messages, incoming]

        # Format messages for LLM consumption
        formatted_messages = self._format_messages_for_llm(person_messages)

        # Call LLM service with formatted messages
        result = await llm_service.complete(
            messages=formatted_messages,
            model=self.llm_config.model,
            api_key_id=self.llm_config.api_key_id,
            service=self.llm_config.service,
            **llm_options,
        )

        # Create the response message
        response_message = Message(
            from_person_id=self.id,
            to_person_id=from_person_id,  # type: ignore[arg-type]
            content=result.text,
            message_type="person_to_person" if from_person_id != "system" else "person_to_system",
            token_count=result.llm_usage.total if result.llm_usage else None,
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
        system_prompt = self.llm_config.system_prompt
        if system_prompt:
            llm_messages.append({"role": "system", "content": system_prompt})

        # Convert domain messages to LLM format
        for msg in messages:
            role = self._determine_message_role(msg)
            llm_messages.append({"role": role, "content": msg.content})

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

    async def complete_with_memory(
        self,
        prompt: str,
        all_messages: list[Message],
        llm_service: "LLMServicePort",
        from_person_id: PersonID | str = "system",
        memorize_to: str | None = None,
        ignore_person: str | None = None,
        at_most: int | None = None,
        prompt_preview: str | None = None,
        **llm_options: Any,
    ) -> tuple[ChatResult, Message, Message, list[Message] | None]:
        """Complete prompt with intelligent memory selection.

        This method consolidates memory selection and completion into a single call,
        using the configured memory strategy to filter messages before completion.

        Args:
            prompt: The prompt to complete
            all_messages: The complete conversation history
            llm_service: The LLM service to use
            from_person_id: The ID of the person sending the prompt
            memorize_to: Optional memory selection criteria (e.g., "recent", "important", "GOLDFISH")
            ignore_person: Optional comma-separated list of person IDs whose messages to exclude
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
        if memorize_to and self._memory_strategy:
            # Use prompt_preview if provided, otherwise use the actual prompt
            preview = prompt_preview or prompt

            # Perform memory selection directly using strategy
            selected_messages = await self._memory_strategy.select_memories(
                candidate_messages=all_messages,
                prompt_preview=preview,
                memorize_to=memorize_to,
                ignore_person=ignore_person,
                at_most=at_most,
                person_id=self.id,
                llm_service=llm_service,
            )

            # Use selected messages if selection was performed
            if selected_messages is not None:
                messages_for_completion = selected_messages

        # Now complete with the messages
        result, incoming, response = await self.complete(
            prompt=prompt,
            all_messages=messages_for_completion,
            llm_service=llm_service,
            from_person_id=from_person_id,
            **llm_options,
        )

        # Return everything including the selected messages for transparency
        return result, incoming, response, selected_messages

    def __repr__(self) -> str:
        memory_info = "with_strategy" if self._memory_strategy else "no_memory"
        return (
            f"Person(id={self.id}, name={self.name}, "
            f"{memory_info}, "
            f"llm={self.llm_config.service}:{self.llm_config.model})"
        )
