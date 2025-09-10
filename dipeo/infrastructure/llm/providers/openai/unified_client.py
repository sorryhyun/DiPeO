"""Unified OpenAI client that merges adapter and wrapper layers."""

import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from dipeo.config.llm import (
    DECISION_EVALUATION_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    MEMORY_SELECTION_MAX_TOKENS,
    OPENAI_MAX_CONTEXT_LENGTH,
    OPENAI_MAX_OUTPUT_TOKENS,
)
from dipeo.config.provider_capabilities import get_provider_capabilities_object
from dipeo.diagram_generated import Message, ToolConfig
from dipeo.diagram_generated.domain_models import LLMUsage
from dipeo.infrastructure.llm.core.types import (
    AdapterConfig,
    ExecutionPhase,
    LLMResponse,
    ProviderCapabilities,
)

logger = logging.getLogger(__name__)


class UnifiedOpenAIClient:
    """Unified OpenAI client that combines adapter and wrapper functionality."""

    def __init__(self, config: AdapterConfig):
        """Initialize unified client with configuration."""
        self.config = config
        self.model = config.model
        self.api_key = config.api_key
        self.provider_type = "openai"

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        # Create clients
        self.sync_client = OpenAI(
            api_key=self.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0,  # We handle retries ourselves
        )
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0,  # We handle retries ourselves
        )

        # Retry configuration
        self.max_retries = config.max_retries or 3
        self.retry_delay = config.retry_delay or 1.0
        self.retry_backoff = config.retry_backoff or 2.0

        # Get provider capabilities from config
        self._capabilities = get_provider_capabilities_object(
            "openai",
            max_context_length=OPENAI_MAX_CONTEXT_LENGTH,
            max_output_tokens=OPENAI_MAX_OUTPUT_TOKENS,
        )

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return self._capabilities

    def supports_feature(self, feature: str) -> bool:
        """Check if provider supports a specific feature."""
        return getattr(self._capabilities, f"supports_{feature}", False)

    def validate_model(self, model: str) -> bool:
        """Validate if model is supported by provider."""
        # Check against supported models in capabilities
        if hasattr(self._capabilities, "supported_models") and self._capabilities.supported_models:
            return model in self._capabilities.supported_models
        # Fallback to prefix checking
        model_lower = model.lower()
        valid_prefixes = ["gpt", "o1", "o3", "dall-e", "whisper", "text-embedding", "embedding"]
        return any(model_lower.startswith(prefix) for prefix in valid_prefixes)

    def _prepare_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert Message objects to API format."""
        result = []
        for msg in messages:
            # Messages should already be dictionaries with proper structure
            if not msg.get("content"):
                continue

            message_dict = {
                "role": msg.get("role", "user"),
                "content": msg["content"],
            }

            # Add name if present
            if msg.get("name"):
                message_dict["name"] = msg["name"]

            result.append(message_dict)
        return result

    def _prepare_tools(self, tools: list[ToolConfig]) -> list[dict[str, Any]]:
        """Convert tool configs to API format."""
        if not tools:
            return None

        api_tools = []
        for tool in tools:
            api_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters if hasattr(tool, "parameters") else {},
                },
            }
            api_tools.append(api_tool)

        return api_tools

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse API response to LLMResponse."""
        # Handle structured output (Pydantic models)
        if hasattr(response, "parsed"):
            return LLMResponse(
                content=response.parsed,
                raw_response=response,
                usage=self._extract_usage(response),
                provider="openai",
                model=self.model,
            )

        # Handle regular response from new responses API
        if hasattr(response, "output_text"):
            # New responses API structure: response.output[0].content[0].text
            output = response.output_text if response.output_text else None
            if output and hasattr(output, "content"):
                content_item = output.content[0] if output.content else None
                if content_item and hasattr(content_item, "text"):
                    text = content_item.text
                else:
                    text = str(content_item) if content_item else ""
            else:
                text = str(output) if output else ""

            return LLMResponse(
                content=text,
                raw_response=response,
                usage=self._extract_usage(response),
                provider="openai",
                model=self.model,
            )

        # Last resort
        return LLMResponse(
            content=str(response),
            raw_response=response,
            usage=None,
            provider="openai",
            model=self.model,
        )

    def _extract_usage(self, response: Any) -> LLMUsage | None:
        """Extract token usage from response."""
        if hasattr(response, "usage"):
            usage = response.usage
            return LLMUsage(
                input=usage.prompt_tokens if hasattr(usage, "prompt_tokens") else 0,
                output=usage.completion_tokens if hasattr(usage, "completion_tokens") else 0,
                total=usage.total_tokens if hasattr(usage, "total_tokens") else 0,
            )
        return None

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
        """Execute async chat completion with retry logic."""
        # Prepare messages
        prepared_messages = self._prepare_messages(messages)

        # Build request parameters
        params = {
            "model": self.model,
            "input": prepared_messages,  # New API uses 'input'
        }

        # Add max tokens (new API parameter name)
        if max_tokens:
            params["max_output_tokens"] = max_tokens
        else:
            params["max_output_tokens"] = self.config.max_tokens or OPENAI_MAX_OUTPUT_TOKENS

        # Add tools if provided
        if tools:
            params["tools"] = self._prepare_tools(tools)

        # Override max_output_tokens for specific execution phases
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            params["max_output_tokens"] = MEMORY_SELECTION_MAX_TOKENS
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            params["max_output_tokens"] = DECISION_EVALUATION_MAX_TOKENS

        # Check for text_format in kwargs (for structured output)
        text_format = kwargs.pop("text_format", None)
        structured_model = response_format or text_format

        # Add remaining kwargs
        kwargs_without_formats = {
            k: v
            for k, v in kwargs.items()
            if k not in ["response_format", "text_format", "messages", "execution_phase"]
        }
        params.update(kwargs_without_formats)

        # Execute with retry
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.retry_delay, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        ):
            with attempt:
                # Handle structured output
                if (
                    structured_model
                    and isinstance(structured_model, type)
                    and issubclass(structured_model, BaseModel)
                ):
                    params["text_format"] = structured_model
                    response = await self.async_client.responses.parse(**params)
                else:
                    response = await self.async_client.responses.create(**params)

                return self._parse_response(response)

    async def stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream chat completion."""
        if not self.capabilities.supports_streaming:
            raise NotImplementedError(f"{self.provider_type} does not support streaming")

        # Prepare messages
        prepared_messages = self._prepare_messages(messages)

        # Build request parameters
        params = {
            "model": self.model,
            "input": prepared_messages,  # New API uses 'input'
            "stream": True,
        }

        # Add max tokens
        if max_tokens:
            params["max_output_tokens"] = max_tokens
        else:
            params["max_output_tokens"] = self.config.max_tokens or OPENAI_MAX_OUTPUT_TOKENS

        # Add tools if provided
        if tools:
            params["tools"] = self._prepare_tools(tools)

        # Add remaining kwargs
        kwargs_filtered = {
            k: v
            for k, v in kwargs.items()
            if k not in ["response_format", "text_format", "messages", "execution_phase"]
        }
        params.update(kwargs_filtered)

        # Execute with retry
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.retry_delay, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        ):
            with attempt:
                stream = await self.async_client.responses.create(**params)
                async for chunk in stream:
                    if hasattr(chunk, "output"):
                        # New responses API structure
                        output = chunk.output[0] if chunk.output else None
                        if output and hasattr(output, "content"):
                            content_item = output.content[0] if output.content else None
                            if content_item and hasattr(content_item, "text"):
                                yield content_item.text
                    elif hasattr(chunk, "choices"):
                        # Fallback for older format
                        choice = chunk.choices[0] if chunk.choices else None
                        if choice and hasattr(choice, "delta"):
                            delta = choice.delta
                            if hasattr(delta, "content") and delta.content:
                                yield delta.content

    async def batch_chat(
        self,
        messages_list: list[list[Message]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: Any | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> list[LLMResponse]:
        """Execute batch chat completion.

        Args:
            messages_list: List of message lists for batch processing
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            tools: Tool configurations
            response_format: Response format specification
            execution_phase: Execution phase context
            **kwargs: Additional parameters

        Returns:
            List of LLM responses

        Raises:
            NotImplementedError: Batch chat is not yet implemented
        """
        raise NotImplementedError("Batch chat is not yet implemented for OpenAI")
