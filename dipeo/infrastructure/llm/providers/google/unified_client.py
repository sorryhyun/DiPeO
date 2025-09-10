"""Unified Google (Gemini) client that merges adapter and wrapper layers."""

import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from dipeo.config.llm import (
    DEFAULT_TEMPERATURE,
    GOOGLE_MAX_CONTEXT_LENGTH,
    GOOGLE_MAX_OUTPUT_TOKENS,
)
from dipeo.config.provider_capabilities import get_provider_capabilities_object
from dipeo.diagram_generated import Message, ToolConfig
from dipeo.diagram_generated.domain_models import LLMUsage
from dipeo.infrastructure.llm.drivers.types import (
    AdapterConfig,
    ExecutionPhase,
    LLMResponse,
    ProviderCapabilities,
)

logger = logging.getLogger(__name__)


class UnifiedGoogleClient:
    """Unified Google (Gemini) client that combines adapter and wrapper functionality."""

    def __init__(self, config: AdapterConfig):
        """Initialize unified client with configuration."""
        self.config = config
        self.model = config.model
        self.api_key = config.api_key or os.getenv("GOOGLE_API_KEY")
        self.provider_type = "google"

        if not self.api_key:
            raise ValueError("Google API key not provided")

        # Create client
        self.client = genai.Client(api_key=self.api_key)

        # Set capabilities
        self.capabilities = self._get_capabilities()

        # Initialize retry configuration
        self.max_retries = config.max_retries or 3
        self.retry_delay = config.retry_delay or 1.0
        self.retry_backoff = config.retry_backoff or 2.0

    def _get_capabilities(self) -> ProviderCapabilities:
        """Get Google provider capabilities."""
        from dipeo.config.provider_capabilities import ProviderType as ConfigProviderType

        return get_provider_capabilities_object(
            ConfigProviderType.GOOGLE,
            max_context_length=GOOGLE_MAX_CONTEXT_LENGTH,
            max_output_tokens=GOOGLE_MAX_OUTPUT_TOKENS,
        )

    def _convert_messages(self, messages: list[Message]) -> tuple[list[dict[str, Any]], str | None]:
        """Convert messages to Gemini format."""
        gemini_messages = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                # Gemini uses system_instruction parameter
                system_instruction = msg.content
            elif msg.role == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": msg.content}]})
            else:  # user role
                gemini_messages.append({"role": "user", "parts": [{"text": msg.content}]})

        return gemini_messages, system_instruction

    def _convert_tools(self, tools: list[ToolConfig] | None) -> list[dict[str, Any]] | None:
        """Convert tool configs to Gemini format."""
        if not tools:
            return None

        gemini_tools = []
        for tool in tools:
            gemini_tool = {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.parameters or {},
            }
            gemini_tools.append(gemini_tool)

        return gemini_tools

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse Gemini response to unified format."""
        # Extract text content
        text_content = ""
        if hasattr(response, "text"):
            text_content = response.text
        elif hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                for part in candidate.content.parts:
                    if hasattr(part, "text"):
                        text_content += part.text

        # Extract usage information
        usage = None
        if hasattr(response, "usage_metadata"):
            usage_data = response.usage_metadata
            usage = LLMUsage(
                input_tokens=getattr(usage_data, "prompt_token_count", 0),
                output_tokens=getattr(usage_data, "candidates_token_count", 0),
                total_tokens=getattr(usage_data, "total_token_count", 0),
            )

        return LLMResponse(
            content=text_content,
            raw_response=response,
            usage=usage,
            model=self.model,
            provider=self.provider_type,
        )

    async def async_chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: type[BaseModel] | dict[str, Any] | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute async chat completion with retry logic."""
        model = model or self.model

        # Convert messages and tools
        gemini_messages, system_instruction = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools)

        # Build generation config
        config_params = {
            "temperature": temperature,
        }
        if max_tokens:
            config_params["max_output_tokens"] = max_tokens

        generation_config = self.client.GenerationConfig(**config_params)

        # Create model with system instruction
        model_obj = self.client.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction,
        )

        # Add tools if provided
        tool_config = None
        if gemini_tools:
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            )

        # Set up retry logic
        retry = AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=self.retry_delay,
                min=self.retry_delay,
                max=self.retry_delay * (self.retry_backoff**self.max_retries),
            ),
            retry=retry_if_exception_type(Exception),
        )

        async def _make_request():
            # Note: Google's SDK doesn't have true async support yet,
            # so we use the sync method. This is a known limitation.
            response = model_obj.generate_content(
                contents=gemini_messages,
                generation_config=generation_config,
                tools=gemini_tools if gemini_tools else None,
                tool_config=tool_config if tool_config else None,
            )
            return self._parse_response(response)

        async for attempt in retry:
            with attempt:
                return await _make_request()

        # Should never reach here due to retry logic
        raise RuntimeError("Failed to get response after retries")

    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: type[BaseModel] | dict[str, Any] | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream chat completion response."""
        model = model or self.model

        # Convert messages and tools
        gemini_messages, system_instruction = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools)

        # Build generation config
        config_params = {
            "temperature": temperature,
        }
        if max_tokens:
            config_params["max_output_tokens"] = max_tokens

        generation_config = self.client.GenerationConfig(**config_params)

        # Create model with system instruction
        model_obj = self.client.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction,
        )

        # Add tools if provided
        tool_config = None
        if gemini_tools:
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            )

        # Make streaming request
        # Note: Google's SDK doesn't have true async streaming yet
        response = model_obj.generate_content(
            contents=gemini_messages,
            generation_config=generation_config,
            tools=gemini_tools if gemini_tools else None,
            tool_config=tool_config if tool_config else None,
            stream=True,
        )

        # Stream chunks
        for chunk in response:
            if hasattr(chunk, "text"):
                yield chunk.text
            elif hasattr(chunk, "candidates") and chunk.candidates:
                candidate = chunk.candidates[0]
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    for part in candidate.content.parts:
                        if hasattr(part, "text"):
                            yield part.text

    async def batch_chat(
        self,
        messages_list: list[list[Message]],
        model: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: type[BaseModel] | dict[str, Any] | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> list[LLMResponse]:
        """Execute batch chat completion requests."""
        # Google doesn't have native batch API, so we process sequentially
        # This can be optimized with asyncio.gather in the future
        raise NotImplementedError("Batch chat not yet implemented for Google provider")
