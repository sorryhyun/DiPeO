"""OpenAI adapter wrapper that uses UnifiedOpenAIClient."""

import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

from dipeo.config.llm import OPENAI_MAX_CONTEXT_LENGTH, OPENAI_MAX_OUTPUT_TOKENS
from dipeo.config.provider_capabilities import (
    ProviderType as ConfigProviderType,
)
from dipeo.config.provider_capabilities import (
    get_provider_capabilities_object,
)
from dipeo.diagram_generated import Message, ToolConfig

from ...capabilities import (
    PhaseHandler,
    RetryHandler,
    StreamingHandler,
    StructuredOutputHandler,
    ToolHandler,
)
from ...core.adapter import UnifiedAdapter
from ...core.types import (
    AdapterConfig,
    ExecutionPhase,
    LLMResponse,
    ProviderCapabilities,
    ProviderType,
    RetryConfig,
    StreamConfig,
)
from ...processors import MessageProcessor, ResponseProcessor
from .unified_client import UnifiedOpenAIClient

logger = logging.getLogger(__name__)


class OpenAIAdapter(UnifiedAdapter):
    """OpenAI adapter that wraps UnifiedOpenAIClient."""

    def __init__(self, config: AdapterConfig):
        """Initialize OpenAI adapter with unified client."""
        # Create unified client
        self.unified_client = UnifiedOpenAIClient(config)

        # Call parent init
        super().__init__(config)

        # Initialize capabilities
        self.tool_handler = ToolHandler(ProviderType.OPENAI)
        self.structured_output_handler = StructuredOutputHandler(ProviderType.OPENAI)
        self.streaming_handler = StreamingHandler(
            ProviderType.OPENAI, StreamConfig(mode=config.streaming_mode)
        )
        self.retry_handler = RetryHandler(
            ProviderType.OPENAI,
            RetryConfig(
                max_attempts=config.max_retries,
                initial_delay=config.retry_delay,
                backoff_factor=config.retry_backoff,
            ),
        )
        self.phase_handler = PhaseHandler(ProviderType.OPENAI)

        # Initialize processors
        self.message_processor = MessageProcessor(ProviderType.OPENAI)
        self.response_processor = ResponseProcessor(ProviderType.OPENAI)

    def _get_capabilities(self) -> ProviderCapabilities:
        """Get OpenAI provider capabilities from centralized config."""
        return get_provider_capabilities_object(
            ConfigProviderType.OPENAI,
            max_context_length=OPENAI_MAX_CONTEXT_LENGTH,
            max_output_tokens=OPENAI_MAX_OUTPUT_TOKENS,
        )

    def _create_sync_client(self):
        """Return the unified client for sync operations."""
        return self.unified_client

    async def _create_async_client(self):
        """Return the unified client for async operations."""
        return self.unified_client

    def validate_model(self, model: str) -> bool:
        """Validate if model is supported."""
        return (
            model in self.capabilities.supported_models
            or model.startswith("gpt-")
            or model.startswith("o1-")
            or model.startswith("o3-")
        )

    def prepare_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Prepare messages for OpenAI API."""
        # Apply phase-specific preparation
        if self.config.execution_phase != ExecutionPhase.DEFAULT:
            messages = self.phase_handler.prepare_messages_for_phase(
                messages, self.config.execution_phase
            )

        # Process messages
        return self.message_processor.prepare_messages(messages)

    def _prepare_tools(self, tools: list[ToolConfig]) -> list[dict[str, Any]]:
        """Prepare tools for OpenAI API."""
        return self.tool_handler.convert_tools_to_api_format(tools)

    def chat(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: Any | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute synchronous chat completion."""
        # Update config execution phase if provided
        if execution_phase:
            self.config.execution_phase = execution_phase

        # Delegate to unified client
        return self.unified_client.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
            execution_phase=execution_phase or self.config.execution_phase,
            **kwargs,
        )

    async def async_chat(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: Any | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute asynchronous chat completion."""
        # Update config execution phase if provided
        if execution_phase:
            self.config.execution_phase = execution_phase

        # Delegate to unified client
        return await self.unified_client.async_chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
            execution_phase=execution_phase or self.config.execution_phase,
            **kwargs,
        )

    def stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Execute streaming chat completion (sync)."""
        # Note: UnifiedOpenAIClient doesn't implement streaming yet
        # For now, return non-streaming response as single chunk
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        )
        yield response.content

    async def async_stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Execute streaming chat completion (async)."""
        # Note: UnifiedOpenAIClient doesn't implement streaming yet
        # For now, return non-streaming response as single chunk
        response = await self.async_chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        )
        yield response.content

    def process_response(self, raw_response: Any) -> LLMResponse:
        """Process raw provider response."""
        # UnifiedOpenAIClient already returns LLMResponse
        if isinstance(raw_response, LLMResponse):
            return raw_response

        # Fallback to response processor
        return self.response_processor.process_response(
            raw_response, self.model, self.provider_type
        )
