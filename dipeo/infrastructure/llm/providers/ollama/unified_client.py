"""Unified Ollama client that merges adapter and wrapper layers."""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import ollama
from ollama import AsyncClient
from pydantic import BaseModel
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from dipeo.config.llm import (
    DEFAULT_TEMPERATURE,
    OLLAMA_MAX_CONTEXT_LENGTH,
    OLLAMA_MAX_OUTPUT_TOKENS,
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


class UnifiedOllamaClient:
    """Unified Ollama client that combines adapter and wrapper functionality."""

    # Class-level cache for model availability
    _model_availability_cache: dict[str, bool] = {}
    _cache_lock: asyncio.Lock | None = None

    def __init__(self, config: AdapterConfig):
        """Initialize unified client with configuration."""
        self.config = config
        self.model = config.model
        self.provider_type = "ollama"

        # Default Ollama server URL
        self.base_url = config.base_url or "http://localhost:11434"

        # Create clients
        self.sync_client = ollama.Client(host=self.base_url)
        self.async_client = AsyncClient(host=self.base_url)

        # Set capabilities
        self.capabilities = self._get_capabilities()

        # Initialize retry configuration
        self.max_retries = config.max_retries or 3
        self.retry_delay = config.retry_delay or 1.0
        self.retry_backoff = config.retry_backoff or 2.0

        # Initialize cache lock if needed
        if UnifiedOllamaClient._cache_lock is None:
            UnifiedOllamaClient._cache_lock = asyncio.Lock()

    def _get_capabilities(self) -> ProviderCapabilities:
        """Get Ollama provider capabilities."""
        from dipeo.config.provider_capabilities import ProviderType as ConfigProviderType

        return get_provider_capabilities_object(
            ConfigProviderType.OLLAMA,
            max_context_length=OLLAMA_MAX_CONTEXT_LENGTH,
            max_output_tokens=OLLAMA_MAX_OUTPUT_TOKENS,
        )

    async def _ensure_model_available(self, model: str) -> bool:
        """Check if model is available locally, pull if not."""
        cache_key = f"{self.base_url}:{model}"

        # Check cache first
        if cache_key in UnifiedOllamaClient._model_availability_cache:
            logger.debug(f"Model {model} availability cached: True")
            return UnifiedOllamaClient._model_availability_cache[cache_key]

        async with UnifiedOllamaClient._cache_lock:
            # Double-check after acquiring lock
            if cache_key in UnifiedOllamaClient._model_availability_cache:
                return UnifiedOllamaClient._model_availability_cache[cache_key]

            try:
                # Check if model exists
                models_list = await self.async_client.list()
                available_models = [
                    m.get("name", "").split(":")[0] for m in models_list.get("models", [])
                ]
                full_model_names = [m.get("name", "") for m in models_list.get("models", [])]

                # Check both base name and full name
                model_base = model.split(":")[0]
                if model_base in available_models or model in full_model_names:
                    logger.debug(f"Model {model} already available locally")
                    UnifiedOllamaClient._model_availability_cache[cache_key] = True
                    return True

                # Try to pull the model
                logger.info(f"Model {model} not found locally, attempting to pull...")
                await self.async_client.pull(model)
                logger.info(f"Successfully pulled model {model}")
                UnifiedOllamaClient._model_availability_cache[cache_key] = True
                return True

            except Exception as e:
                logger.error(f"Failed to ensure model {model} is available: {e}")
                return False

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert messages to Ollama format."""
        ollama_messages = []

        for msg in messages:
            ollama_msg = {
                "role": msg.role,
                "content": msg.content,
            }

            # Handle tool calls if present
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                ollama_msg["tool_calls"] = msg.tool_calls

            # Handle tool response
            if msg.role == "tool" and hasattr(msg, "tool_call_id"):
                ollama_msg["tool_call_id"] = msg.tool_call_id

            ollama_messages.append(ollama_msg)

        return ollama_messages

    def _convert_tools(self, tools: list[ToolConfig] | None) -> list[dict[str, Any]] | None:
        """Convert tool configs to Ollama format."""
        if not tools:
            return None

        ollama_tools = []
        for tool in tools:
            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.parameters or {},
                },
            }
            ollama_tools.append(ollama_tool)

        return ollama_tools

    def _parse_response(self, response: dict[str, Any]) -> LLMResponse:
        """Parse Ollama response to unified format."""
        # Extract content from response
        message = response.get("message", {})
        content = message.get("content", "")

        # Extract usage information
        usage = None
        if "prompt_eval_count" in response or "eval_count" in response:
            usage = LLMUsage(
                input_tokens=response.get("prompt_eval_count", 0),
                output_tokens=response.get("eval_count", 0),
                total_tokens=response.get("prompt_eval_count", 0) + response.get("eval_count", 0),
            )

        return LLMResponse(
            content=content,
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

        # Ensure model is available
        if not await self._ensure_model_available(model):
            raise ValueError(f"Failed to ensure model {model} is available")

        # Convert messages and tools
        ollama_messages = self._convert_messages(messages)
        ollama_tools = self._convert_tools(tools)

        # Build options
        options = {
            "temperature": temperature,
        }
        if max_tokens:
            options["num_predict"] = max_tokens

        # Build request
        request_params = {
            "model": model,
            "messages": ollama_messages,
            "options": options,
            "stream": False,
        }

        if ollama_tools:
            request_params["tools"] = ollama_tools

        if response_format:
            if isinstance(response_format, type) and issubclass(response_format, BaseModel):
                # Convert Pydantic model to JSON schema
                request_params["format"] = response_format.model_json_schema()
            elif isinstance(response_format, dict):
                request_params["format"] = response_format

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
            response = await self.async_client.chat(**request_params)
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

        # Ensure model is available
        if not await self._ensure_model_available(model):
            raise ValueError(f"Failed to ensure model {model} is available")

        # Convert messages and tools
        ollama_messages = self._convert_messages(messages)
        ollama_tools = self._convert_tools(tools)

        # Build options
        options = {
            "temperature": temperature,
        }
        if max_tokens:
            options["num_predict"] = max_tokens

        # Build request
        request_params = {
            "model": model,
            "messages": ollama_messages,
            "options": options,
            "stream": True,
        }

        if ollama_tools:
            request_params["tools"] = ollama_tools

        if response_format:
            if isinstance(response_format, type) and issubclass(response_format, BaseModel):
                # Convert Pydantic model to JSON schema
                request_params["format"] = response_format.model_json_schema()
            elif isinstance(response_format, dict):
                request_params["format"] = response_format

        # Stream response
        async for chunk in await self.async_client.chat(**request_params):
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]

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
        # Ollama doesn't have native batch API, so we process with asyncio.gather
        tasks = [
            self.async_chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                response_format=response_format,
                execution_phase=execution_phase,
                **kwargs,
            )
            for messages in messages_list
        ]

        return await asyncio.gather(*tasks)
