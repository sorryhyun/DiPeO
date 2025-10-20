"""Person dynamic object representing an LLM agent with evolving conversation state."""

from typing import TYPE_CHECKING, Any, Optional

from dipeo.diagram_generated import (
    ChatResult,
    LLMService,
    Message,
    PersonLLMConfig,
)
from dipeo.diagram_generated.domain_models import PersonID
from dipeo.infrastructure.timing.context import atime_phase, time_phase

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
        """Get memory configuration information."""
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

        Handles message formatting and system prompts internally before delegating to LLM service.
        Returns (ChatResult, incoming_message, response_message).
        """
        trace_id = llm_options.get("trace_id", llm_options.get("execution_id", ""))
        node_id = llm_options.get("node_id", str(self.id))

        with time_phase(trace_id, node_id, "direct_execution__message_prep"):
            incoming = Message(
                from_person_id=from_person_id,  # type: ignore[arg-type]
                to_person_id=self.id,
                content=prompt,
                message_type="person_to_person"
                if from_person_id != "system"
                else "system_to_person",
            )

            person_messages = [*all_messages, incoming]

            formatted_messages = self._format_messages_for_llm(person_messages)

        async with atime_phase(trace_id, node_id, "direct_execution__api_call"):
            result = await llm_service.complete(
                messages=formatted_messages,
                model=self.llm_config.model,
                api_key_id=self.llm_config.api_key_id,
                service_name=self.llm_config.service,
                **llm_options,
            )

        with time_phase(trace_id, node_id, "direct_execution__response_build"):
            response_message = Message(
                from_person_id=self.id,
                to_person_id=from_person_id,  # type: ignore[arg-type]
                content=result.text,
                message_type="person_to_person"
                if from_person_id != "system"
                else "person_to_system",
                token_count=result.llm_usage.total if result.llm_usage else None,
            )

        return result, incoming, response_message

    def _format_messages_for_llm(self, messages: list[Message]) -> list[dict[str, str]]:
        """Format domain messages for LLM consumption with role and content keys."""
        llm_messages = []

        system_prompt = self.llm_config.system_prompt
        if system_prompt:
            llm_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            role = self._determine_message_role(msg)
            llm_messages.append({"role": role, "content": msg.content})

        return llm_messages

    def _determine_message_role(self, message: Message) -> str:
        """Determine the LLM role (user/assistant) for a message."""
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
        execution_id: str | None = None,
        node_id: str | None = None,
        **llm_options: Any,
    ) -> tuple[ChatResult, Message, Message, list[Message] | None]:
        """Complete prompt with intelligent memory selection using configured strategy.

        Consolidates memory filtering and LLM completion in a single call.
        Returns (ChatResult, incoming_message, response_message, selected_messages).
        selected_messages is None if no memorize_to criteria provided, [] for GOLDFISH mode.
        """
        exec_id = execution_id or ""

        async with atime_phase(exec_id, str(self.id), "person_complete_with_memory"):
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
                    execution_id=exec_id,
                    node_id=node_id,
                )

                if selected_messages is not None:
                    messages_for_completion = selected_messages

            result, incoming, response = await self.complete(
                prompt=prompt,
                all_messages=messages_for_completion,
                llm_service=llm_service,
                from_person_id=from_person_id,
                **llm_options,
            )

            return result, incoming, response, selected_messages

    def __repr__(self) -> str:
        memory_info = "with_strategy" if self._memory_strategy else "no_memory"
        return (
            f"Person(id={self.id}, name={self.name}, "
            f"{memory_info}, "
            f"llm={self.llm_config.service}:{self.llm_config.model})"
        )
