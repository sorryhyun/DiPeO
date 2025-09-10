"""Unified Anthropic client that merges adapter and wrapper layers."""

import logging
import os
from collections.abc import AsyncIterator
from typing import Any

import anthropic
from pydantic import BaseModel
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from dipeo.config.llm import (
    DECISION_EVALUATION_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    MEMORY_SELECTION_MAX_TOKENS,
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


class UnifiedAnthropicClient:
    """Unified Anthropic client that combines adapter and wrapper functionality."""

    def __init__(self, config: AdapterConfig):
        """Initialize unified client with configuration."""
        self.config = config
        self.model = config.model
        self.api_key = config.api_key
        self.provider_type = "anthropic"

        if not self.api_key:
            raise ValueError("Anthropic API key not provided")

        # Create clients
        self.sync_client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0,  # We handle retries ourselves
        )
        self.async_client = anthropic.AsyncAnthropic(
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
            "anthropic",
            max_context_length=200000,  # Claude's context window
            max_output_tokens=4096,  # Claude's default max output
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
        return (
            "claude" in model_lower
            or "haiku" in model_lower
            or "sonnet" in model_lower
            or "opus" in model_lower
        )

    def _prepare_messages(self, messages: list[Message]) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert Message objects to Anthropic format (system prompt + messages)."""
        system_prompt = None
        api_messages = []

        for msg in messages:
            # Skip empty messages
            content = msg.content if hasattr(msg, "content") else str(msg)
            if not content:
                continue

            role = msg.role if hasattr(msg, "role") else "user"

            # Extract system prompt
            if role == "system":
                if system_prompt:
                    system_prompt += "\n\n" + content
                else:
                    system_prompt = content
            else:
                # Convert to Anthropic format
                if role == "user":
                    api_role = "user"
                elif role in ["assistant", "model"]:
                    api_role = "assistant"
                else:
                    api_role = "user"  # Default to user

                api_messages.append({"role": api_role, "content": content})

        return system_prompt, api_messages

    def _prepare_tools(self, tools: list[ToolConfig]) -> list[dict[str, Any]]:
        """Convert tool configs to Anthropic format."""
        if not tools:
            return None

        api_tools = []
        for tool in tools:
            api_tool = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters
                if hasattr(tool, "parameters")
                else {"type": "object", "properties": {}, "required": []},
            }
            api_tools.append(api_tool)

        return api_tools

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse API response to LLMResponse."""
        # Extract content from response
        if hasattr(response, "content"):
            if isinstance(response.content, list) and response.content:
                # Handle multiple content blocks
                content_parts = []
                for block in response.content:
                    if hasattr(block, "text"):
                        content_parts.append(block.text)
                    elif hasattr(block, "type") and block.type == "text":
                        content_parts.append(block.text if hasattr(block, "text") else str(block))
                    else:
                        content_parts.append(str(block))
                content = "\n".join(content_parts)
            elif isinstance(response.content, str):
                content = response.content
            else:
                content = str(response.content)
        else:
            content = str(response)

        return LLMResponse(
            content=content,
            raw_response=response,
            usage=self._extract_usage(response),
            provider="anthropic",
            model=self.model,
        )

    def _extract_usage(self, response: Any) -> LLMUsage | None:
        """Extract token usage from response."""
        if hasattr(response, "usage"):
            usage = response.usage
            return LLMUsage(
                input=usage.input_tokens if hasattr(usage, "input_tokens") else 0,
                output=usage.output_tokens if hasattr(usage, "output_tokens") else 0,
                total=(
                    (usage.input_tokens if hasattr(usage, "input_tokens") else 0)
                    + (usage.output_tokens if hasattr(usage, "output_tokens") else 0)
                ),
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
        system_prompt, prepared_messages = self._prepare_messages(messages)

        # Build request parameters
        params = {
            "model": self.model,
            "messages": prepared_messages,
            "max_tokens": max_tokens or self.config.max_tokens or 4096,
        }

        # Add system prompt if present
        if system_prompt:
            params["system"] = system_prompt

        # Add temperature if specified
        if temperature is not None:
            params["temperature"] = temperature
        elif self.config.temperature is not None:
            params["temperature"] = self.config.temperature

        # Add tools if provided
        if tools:
            params["tools"] = self._prepare_tools(tools)

        # Override max_tokens for specific execution phases
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            params["max_tokens"] = MEMORY_SELECTION_MAX_TOKENS
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            params["max_tokens"] = DECISION_EVALUATION_MAX_TOKENS

        # Add remaining kwargs (but filter out ones we handle)
        kwargs_filtered = {
            k: v
            for k, v in kwargs.items()
            if k not in ["messages", "execution_phase", "text_format", "response_format"]
        }
        params.update(kwargs_filtered)

        # Execute with retry
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.retry_delay, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        ):
            with attempt:
                response = await self.async_client.messages.create(**params)
                return self._parse_response(response)

    async def stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream async chat completion."""
        if not self.capabilities.supports_streaming:
            raise NotImplementedError(f"{self.provider_type} does not support streaming")

        # Prepare messages
        system_prompt, prepared_messages = self._prepare_messages(messages)

        # Build request parameters
        params = {
            "model": self.model,
            "messages": prepared_messages,
            "max_tokens": max_tokens or self.config.max_tokens or 4096,
            "stream": True,
        }

        # Add system prompt if present
        if system_prompt:
            params["system"] = system_prompt

        # Add temperature if specified
        if temperature is not None:
            params["temperature"] = temperature
        elif self.config.temperature is not None:
            params["temperature"] = self.config.temperature

        # Add tools if provided
        if tools:
            params["tools"] = self._prepare_tools(tools)

        # Add remaining kwargs (but filter out ones we handle)
        kwargs_filtered = {
            k: v
            for k, v in kwargs.items()
            if k not in ["messages", "execution_phase", "text_format", "response_format"]
        }
        params.update(kwargs_filtered)

        # Execute with retry
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.retry_delay, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        ):
            with attempt:
                stream = await self.async_client.messages.create(**params)
                async for chunk in stream:
                    if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                        yield chunk.delta.text
                    elif hasattr(chunk, "content_block") and hasattr(chunk.content_block, "text"):
                        yield chunk.content_block.text

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
        raise NotImplementedError("Batch chat is not yet implemented for Anthropic")
