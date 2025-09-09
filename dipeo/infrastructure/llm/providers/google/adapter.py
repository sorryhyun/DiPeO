"""Google AI adapter implementation."""

import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

from google.genai import types

from dipeo.config.llm import GOOGLE_MAX_CONTEXT_LENGTH, GOOGLE_MAX_OUTPUT_TOKENS
from dipeo.config.provider_capabilities import (
    ProviderType as ConfigProviderType,
)
from dipeo.config.provider_capabilities import (
    get_provider_capabilities_object,
)
from dipeo.diagram_generated import Message, ToolConfig
from dipeo.diagram_generated.domain_models import LLMUsage

from ...capabilities import (
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
    StreamingMode,
)
from ...processors import MessageProcessor, ResponseProcessor
from .client import AsyncGoogleClientWrapper, GoogleClientWrapper

logger = logging.getLogger(__name__)


class GoogleAdapter(UnifiedAdapter):
    """Unified Google AI/Gemini adapter with all capabilities."""

    def __init__(self, config: AdapterConfig):
        """Initialize Google adapter with capabilities."""
        # Initialize clients first (before calling super().__init__)
        self.sync_client_wrapper = GoogleClientWrapper(config)
        self.async_client_wrapper = AsyncGoogleClientWrapper(config)

        # Now call parent init
        super().__init__(config)

        # Initialize capabilities
        self.tool_handler = ToolHandler(ProviderType.GOOGLE)
        self.structured_output_handler = StructuredOutputHandler(ProviderType.GOOGLE)
        self.streaming_handler = StreamingHandler(
            ProviderType.GOOGLE, StreamConfig(mode=config.streaming_mode or StreamingMode.SSE)
        )
        self.retry_handler = RetryHandler(
            ProviderType.GOOGLE,
            RetryConfig(
                max_attempts=config.max_retries or 3,
                initial_delay=config.retry_delay or 1.0,
                backoff_factor=config.retry_backoff or 2.0,
            ),
        )

        # Initialize processors
        self.message_processor = MessageProcessor(ProviderType.GOOGLE)
        self.response_processor = ResponseProcessor(ProviderType.GOOGLE)

    def _get_capabilities(self) -> ProviderCapabilities:
        """Get Google provider capabilities from centralized config."""
        return get_provider_capabilities_object(
            ConfigProviderType.GOOGLE,
            max_context_length=GOOGLE_MAX_CONTEXT_LENGTH,
            max_output_tokens=GOOGLE_MAX_OUTPUT_TOKENS,
        )

    def _create_sync_client(self):
        """Create synchronous client."""
        return self.sync_client_wrapper

    async def _create_async_client(self):
        """Create asynchronous client."""
        return self.async_client_wrapper

    def validate_model(self, model: str) -> bool:
        """Validate if model is supported."""
        return model in self.capabilities.supported_models or model.startswith("gemini")

    def prepare_messages(self, messages: list[Message]) -> tuple[list[dict[str, Any]], str | None]:
        """Prepare messages for Google AI API, extracting system prompt."""
        # Extract system prompt (Google handles it separately)
        system_prompt = self.message_processor.extract_system_prompt(messages)

        # Filter out system messages and process the rest
        non_system_messages = [msg for msg in messages if msg.role != "system"]
        prepared_messages = self.message_processor.prepare_messages(non_system_messages)

        return prepared_messages, system_prompt

    def _prepare_tools(self, tools: list[ToolConfig]) -> list[types.Tool]:
        """Prepare tools for Google AI API."""
        if not tools:
            return None

        function_declarations = []

        for tool in tools:
            tool_type = tool.type if isinstance(tool.type, str) else tool.type.value

            if tool_type == "web_search" or tool_type == "web_search_preview":
                # Define web search function
                function_declarations.append(
                    types.FunctionDeclaration(
                        name="web_search",
                        description="Search the web for current information",
                        parameters={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search query"}
                            },
                            "required": ["query"],
                        },
                    )
                )
            elif tool_type == "image_generation":
                # Define image generation function
                function_declarations.append(
                    types.FunctionDeclaration(
                        name="generate_image",
                        description="Generate an image based on a text prompt",
                        parameters={
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The image generation prompt",
                                },
                                "size": {
                                    "type": "string",
                                    "description": "Image size (e.g., 1024x1024)",
                                    "default": "1024x1024",
                                },
                            },
                            "required": ["prompt"],
                        },
                    )
                )
            elif hasattr(tool, "function"):
                # Custom function tool
                func = tool.function
                function_declarations.append(
                    types.FunctionDeclaration(
                        name=func.name,
                        description=func.description,
                        parameters=func.parameters if hasattr(func, "parameters") else {},
                    )
                )

        return (
            [types.Tool(function_declarations=function_declarations)]
            if function_declarations
            else None
        )

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
        """Execute synchronous chat completion with retry logic."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)

        # Validate token limit
        # Token validation is now handled by the API itself

        # Prepare tools
        api_tools = self._prepare_tools(tools) if tools else None

        # Execute with retry
        @self.retry_handler.with_retry
        def _execute():
            return self.sync_client_wrapper.chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=api_tools,
                response_format=response_format,
                system=system_prompt,
                **kwargs,
            )

        raw_response = _execute()

        # Process response
        text = ""
        tool_outputs = []

        if raw_response.candidates:
            candidate = raw_response.candidates[0]
            if candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        text += part.text
                    elif hasattr(part, "function_call") and part.function_call:
                        # Process function call
                        tool_output = self.tool_handler.process_tool_outputs(part.function_call)
                        if tool_output:
                            tool_outputs.append(tool_output)

        # Extract token usage
        token_usage = None
        if hasattr(raw_response, "usage_metadata"):
            usage = raw_response.usage_metadata
            if hasattr(usage, "prompt_token_count") and hasattr(usage, "candidates_token_count"):
                token_usage = LLMUsage(
                    input=usage.prompt_token_count,
                    output=usage.candidates_token_count,
                    total=usage.prompt_token_count + usage.candidates_token_count,
                )

        response = LLMResponse(
            text=text,
            raw_response=raw_response,
            token_usage=token_usage,
            tool_outputs=tool_outputs if tool_outputs else None,
        )

        return response

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
        """Execute asynchronous chat completion with retry logic."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)

        # Validate token limit
        # Token validation is now handled by the API itself

        # Prepare tools
        api_tools = self._prepare_tools(tools) if tools else None

        # Execute with retry
        @self.retry_handler.with_async_retry
        async def _execute():
            return await self.async_client_wrapper.chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=api_tools,
                response_format=response_format,
                system=system_prompt,
                **kwargs,
            )

        raw_response = await _execute()

        # Process response
        text = ""
        tool_outputs = []

        if raw_response.candidates:
            candidate = raw_response.candidates[0]
            if candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        text += part.text
                    elif hasattr(part, "function_call") and part.function_call:
                        # Process function call
                        tool_output = self.tool_handler.process_tool_outputs(part.function_call)
                        if tool_output:
                            tool_outputs.append(tool_output)

        # Extract token usage
        token_usage = None
        if hasattr(raw_response, "usage_metadata"):
            usage = raw_response.usage_metadata
            if hasattr(usage, "prompt_token_count") and hasattr(usage, "candidates_token_count"):
                token_usage = LLMUsage(
                    input=usage.prompt_token_count,
                    output=usage.candidates_token_count,
                    total=usage.prompt_token_count + usage.candidates_token_count,
                )

        response = LLMResponse(
            text=text,
            raw_response=raw_response,
            token_usage=token_usage,
            tool_outputs=tool_outputs if tool_outputs else None,
        )

        return response

    def stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Stream synchronous chat completion."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)

        # Prepare tools
        api_tools = self._prepare_tools(tools) if tools else None

        # Execute with retry
        @self.retry_handler.with_retry
        def _execute():
            return self.sync_client_wrapper.stream_chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=api_tools,
                system=system_prompt,
                **kwargs,
            )

        stream = _execute()

        # Process stream chunks
        for chunk in stream:
            if chunk.candidates:
                candidate = chunk.candidates[0]
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text:
                            yield part.text

    async def async_stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream asynchronous chat completion."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)

        # Prepare tools
        api_tools = self._prepare_tools(tools) if tools else None

        # Execute with retry
        @self.retry_handler.with_async_retry
        async def _execute():
            return await self.async_client_wrapper.stream_chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=api_tools,
                system=system_prompt,
                **kwargs,
            )

        stream = await _execute()

        # Process stream chunks
        async for chunk in stream:
            if chunk.candidates:
                candidate = chunk.candidates[0]
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text:
                            yield part.text
