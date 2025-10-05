"""Simplified LLM service that directly uses unified provider clients."""

from typing import Any

from dipeo.config import normalize_service_name
from dipeo.config.services import LLMServiceName
from dipeo.diagram_generated import ChatResult
from dipeo.domain.base import LLMServiceError
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin
from dipeo.domain.integrations.ports import APIKeyPort
from dipeo.domain.integrations.ports import LLMService as LLMServicePort
from dipeo.infrastructure.llm.drivers.client_manager import ClientManager
from dipeo.infrastructure.llm.drivers.completion_handlers import CompletionHandlers
from dipeo.infrastructure.llm.drivers.decision_parser import DecisionParser
from dipeo.infrastructure.llm.drivers.response_converter import ResponseConverter
from dipeo.infrastructure.llm.drivers.types import (
    DecisionOutput,
    LLMResponse,
    MemorySelectionOutput,
)
from dipeo.infrastructure.timing.context import atime_phase


class LLMInfraService(LoggingMixin, InitializationMixin, LLMServicePort):
    """LLM service that directly manages provider clients using composition."""

    def __init__(self, api_key_service: APIKeyPort):
        super().__init__()
        self.api_key_service = api_key_service

        # Composed components
        self._client_manager = ClientManager(api_key_service)
        self._response_converter = ResponseConverter()
        self._decision_parser = DecisionParser()
        self._completion_handlers = CompletionHandlers(
            complete_fn=self.complete,
            decision_parser=self._decision_parser,
        )

    async def initialize(self) -> None:
        pass

    async def complete_memory_selection(
        self,
        candidate_messages: list[Any],
        task_preview: str,
        criteria: str,
        at_most: int | None,
        model: str,
        api_key_id: str,
        service_name: str,
        **kwargs,
    ) -> MemorySelectionOutput:
        """Delegate to completion handlers."""
        return await self._completion_handlers.complete_memory_selection(
            candidate_messages=candidate_messages,
            task_preview=task_preview,
            criteria=criteria,
            at_most=at_most,
            model=model,
            api_key_id=api_key_id,
            service_name=service_name,
            **kwargs,
        )

    async def complete_decision(
        self,
        prompt: str,
        context: dict[str, Any],
        model: str,
        api_key_id: str,
        service_name: str,
        **kwargs,
    ) -> DecisionOutput:
        """Delegate to completion handlers."""
        return await self._completion_handlers.complete_decision(
            prompt=prompt,
            context=context,
            model=model,
            api_key_id=api_key_id,
            service_name=service_name,
            **kwargs,
        )

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        api_key_id: str,
        service_name: str | None = None,
        **kwargs,
    ) -> ChatResult:
        try:
            if messages is None:
                messages = []

            execution_phase = kwargs.pop("execution_phase", None)

            # Use the explicit service parameter if provided, otherwise infer from model
            if service_name:
                if hasattr(service_name, "value"):
                    service_name = service_name.value
                service_name = normalize_service_name(str(service_name))

            # Extract trace_id for timing (if available)
            trace_id = kwargs.get("trace_id", "")

            # Time client pool operations
            async with atime_phase(
                trace_id, "client_manager", f"get_client__{service_name}", service=service_name, model=model
            ):
                client = await self._client_manager.get_client(service_name, model, api_key_id)

            # Filter out provider-specific parameters (keep trace_id for timing)
            filtered_params = {"person_name", "execution_id"}
            client_kwargs = {k: v for k, v in kwargs.items() if k not in filtered_params}

            # Add person_name back only for Claude Code
            if service_name == "claude-code" and "person_name" in kwargs:
                client_kwargs["person_name"] = kwargs["person_name"]

            # Ensure trace_id is passed to client for timing
            if trace_id:
                client_kwargs["trace_id"] = trace_id

            if execution_phase:
                client_kwargs["execution_phase"] = execution_phase
            else:
                from dipeo.diagram_generated.enums import ExecutionPhase

                client_kwargs["execution_phase"] = ExecutionPhase.DIRECT_EXECUTION

            # Time the LLM API call with hierarchical phase names
            execution_phase_obj = client_kwargs.get("execution_phase", "unknown")
            # Use enum value if available, otherwise convert to string
            if hasattr(execution_phase_obj, "value"):
                execution_phase_str = execution_phase_obj.value
            else:
                execution_phase_str = str(execution_phase_obj)

            hierarchical_phase = f"{execution_phase_str}__api_call"

            async with atime_phase(
                trace_id,
                "llm_service",
                hierarchical_phase,
                model=model,
                service=service_name,
                execution_phase=execution_phase_str,
                call_type="api_call",
            ):
                response = await client.async_chat(messages=messages, **client_kwargs)

            if hasattr(self, "logger") and response:
                # Enhanced logging to properly display LLM responses
                if isinstance(response, LLMResponse):
                    if response.content:
                        response_text = str(response.content)[:500]
                    else:
                        response_text = f"<empty content> (structured_output: {response.structured_output is not None})"
                elif hasattr(response, "content"):
                    content = getattr(response, "content", None)
                    if content:
                        response_text = str(content)[:500]
                    else:
                        response_text = "<empty content attribute>"
                elif hasattr(response, "text"):
                    text = getattr(response, "text", None)
                    if text:
                        response_text = str(text)[:500]
                    else:
                        response_text = "<empty text attribute>"
                else:
                    response_text = (
                        f"<unexpected type: {type(response).__name__}> {str(response)[:500]}"
                    )

                self.log_debug(f"LLM response: {response_text}")

            if isinstance(response, LLMResponse):
                return self._response_converter.convert_to_chat_result(response)
            elif isinstance(response, ChatResult):
                return response
            else:
                if hasattr(response, "content"):
                    content = response.content
                elif hasattr(response, "text"):
                    content = response.text
                else:
                    content = str(response)

                result = ChatResult(content=content)

                if hasattr(response, "prompt_tokens"):
                    result.prompt_tokens = response.prompt_tokens
                if hasattr(response, "completion_tokens"):
                    result.completion_tokens = response.completion_tokens
                if hasattr(response, "total_tokens"):
                    result.total_tokens = response.total_tokens

                return result

        except Exception as e:
            if hasattr(self, "logger"):
                self.log_error(f"Error in LLM completion: {e}")
            raise LLMServiceError(service=service_name, message=str(e)) from e

    async def validate_api_key(self, api_key_id: str, service: str | None = None) -> bool:
        """Validate an API key is functional."""
        try:
            # Get the actual API key
            api_key = await self.api_key_service.get_api_key(api_key_id)
            if not api_key:
                return False

            # If service not specified, try a simple test with OpenAI
            if not service:
                service = LLMServiceName.OPENAI.value

            # Try to create a client and test with a simple message
            client = await self._client_manager.get_client(service, "gpt-4o-mini", api_key_id)
            test_response = await client.async_chat(
                messages=[{"role": "user", "content": "test"}], max_output_tokens=1
            )
            return test_response is not None
        except Exception:
            return False
