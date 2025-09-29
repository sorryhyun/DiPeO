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
    from dipeo.domain.conversation.memory_strategies import IntelligentMemoryStrategy
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
        memory_strategy: Optional["IntelligentMemoryStrategy"] = None,
    ):
        self.id = id
        self.name = name
        self.llm_config = llm_config

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
        incoming = Message(
            from_person_id=from_person_id,  # type: ignore[arg-type]
            to_person_id=self.id,
            content=prompt,
            message_type="person_to_person" if from_person_id != "system" else "system_to_person",
        )

        person_messages = [*all_messages, incoming]

        formatted_messages = self._format_messages_for_llm(person_messages)

        result = await llm_service.complete(
            messages=formatted_messages,
            model=self.llm_config.model,
            api_key_id=self.llm_config.api_key_id,
            service_name=self.llm_config.service,
            **llm_options,
        )

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

        system_prompt = self.llm_config.system_prompt
        if system_prompt:
            llm_messages.append({"role": "system", "content": system_prompt})

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
        if message.from_person_id == self.id:
            return "assistant"
        elif message.to_person_id == self.id:
            return "user"
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
        selected_messages = None
        messages_for_completion = all_messages

        if memorize_to and self._memory_strategy:
            preview = prompt_preview or prompt

            selected_messages = await self._memory_strategy.select_memories(
                candidate_messages=all_messages,
                prompt_preview=preview,
                memorize_to=memorize_to,
                ignore_person=ignore_person,
                at_most=at_most,
                person_id=self.id,
                llm_service=llm_service,
            )

            if selected_messages is not None:
                service_name = getattr(self.llm_config.service, "value", self.llm_config.service)
                if isinstance(service_name, str) and service_name.lower() == "claude_code":
                    messages_for_completion = [
                        self._build_memory_tool_result_message(selected_messages)
                    ]
                else:
                    messages_for_completion = selected_messages

        result, incoming, response = await self.complete(
            prompt=prompt,
            all_messages=messages_for_completion,
            llm_service=llm_service,
            from_person_id=from_person_id,
            **llm_options,
        )

        return result, incoming, response, selected_messages

    def _build_memory_tool_result_message(self, selected_messages: list[Message]) -> Message:
        """Create a synthetic tool result message for Claude Code memory selection."""

        from textwrap import shorten

        message_entries: list[dict[str, Any]] = []
        message_ids: list[str] = []
        summary_lines: list[str] = []

        for index, msg in enumerate(selected_messages, start=1):
            message_id = str(msg.id) if getattr(msg, "id", None) else f"memory_{index}"
            message_ids.append(message_id)

            sender = str(getattr(msg, "from_person_id", "unknown"))
            recipient = str(getattr(msg, "to_person_id", "unknown"))
            snippet = shorten((msg.content or "").replace("\n", " ").strip(), width=200, placeholder="…")
            summary_lines.append(f"- {message_id} ({sender} → {recipient}): {snippet}")

            message_entries.append(
                {
                    "id": message_id,
                    "from_person_id": sender,
                    "to_person_id": recipient,
                    "content": msg.content,
                    "timestamp": getattr(msg, "timestamp", None),
                }
            )

        if summary_lines:
            summary_text = "Memory selection tool returned the following messages:\n" + "\n".join(summary_lines)
        else:
            summary_text = "Memory selection tool returned no messages."

        metadata = {
            "claude_code": {
                "tool_result": {
                    "tool_name": "select_memory_messages",
                    "tool_use_id": "dipeo_memory_selection",
                    "result": {
                        "message_ids": message_ids,
                        "messages": message_entries,
                    },
                }
            }
        }

        return Message(
            from_person_id=self.id,
            to_person_id=self.id,
            content=summary_text,
            message_type="person_to_person",
            metadata=metadata,
        )

    def __repr__(self) -> str:
        memory_info = "with_strategy" if self._memory_strategy else "no_memory"
        return (
            f"Person(id={self.id}, name={self.name}, "
            f"{memory_info}, "
            f"llm={self.llm_config.service}:{self.llm_config.model})"
        )
