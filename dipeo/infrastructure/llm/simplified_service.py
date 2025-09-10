"""Simplified LLM service that directly uses unified provider clients."""

import asyncio
import hashlib
import time
from typing import Any

from dipeo.config import VALID_LLM_SERVICES, get_settings, normalize_service_name
from dipeo.config.services import LLMServiceName
from dipeo.diagram_generated import ChatResult
from dipeo.domain.base import APIKeyError, LLMServiceError
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin
from dipeo.domain.integrations.ports import APIKeyPort
from dipeo.domain.integrations.ports import LLMService as LLMServicePort
from dipeo.infrastructure.llm.core.types import AdapterConfig, LLMResponse
from dipeo.infrastructure.shared.drivers.utils import SingleFlightCache


class SimplifiedLLMService(LoggingMixin, InitializationMixin, LLMServicePort):
    """Simplified LLM service that directly manages provider clients."""

    def __init__(self, api_key_service: APIKeyPort):
        self.api_key_service = api_key_service
        self._client_pool: dict[str, dict[str, Any]] = {}
        self._client_pool_lock = asyncio.Lock()
        self._client_cache = SingleFlightCache()  # For deduplicating client creation
        self._settings = get_settings()

        # Model-specific keywords for provider inference
        self._model_keywords = {
            "gpt": LLMServiceName.OPENAI.value,
            "o1": LLMServiceName.OPENAI.value,
            "o3": LLMServiceName.OPENAI.value,
            "dall-e": LLMServiceName.OPENAI.value,
            "whisper": LLMServiceName.OPENAI.value,
            "embedding": LLMServiceName.OPENAI.value,
            "haiku": LLMServiceName.ANTHROPIC.value,
            "sonnet": LLMServiceName.ANTHROPIC.value,
            "opus": LLMServiceName.ANTHROPIC.value,
            "claude": LLMServiceName.ANTHROPIC.value,
            "bison": LLMServiceName.GOOGLE.value,
            "palm": LLMServiceName.GOOGLE.value,
            "gemini": LLMServiceName.GOOGLE.value,
            "llama": LLMServiceName.OLLAMA.value,
            "mistral": LLMServiceName.OLLAMA.value,
            "mixtral": LLMServiceName.OLLAMA.value,
            "gemma": LLMServiceName.OLLAMA.value,
            "phi": LLMServiceName.OLLAMA.value,
            "qwen": LLMServiceName.OLLAMA.value,
        }

    async def initialize(self) -> None:
        """Initialize the service."""
        pass

    def _get_api_key(self, api_key_id: str) -> str:
        """Get API key from the key service."""
        try:
            api_key_data = self.api_key_service.get_api_key(api_key_id)
            return api_key_data["key"]
        except APIKeyError as e:
            raise LLMServiceError(
                service="api_key_service", message=f"Failed to get API key: {e}"
            ) from e

    def _create_cache_key(self, provider: str, model: str, api_key_id: str) -> str:
        """Create a cache key for the client."""
        key_string = f"{provider}:{model}:{api_key_id}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _infer_service_from_model(self, model: str) -> str:
        """Infer service provider from model name."""
        model_lower = model.lower()

        # Check model keywords
        for keyword, service in self._model_keywords.items():
            if keyword in model_lower:
                return service

        # Default to OpenAI for unknown models
        return LLMServiceName.OPENAI.value

    def _create_provider_client(
        self, provider: str, model: str, api_key: str, base_url: str | None = None
    ) -> Any:
        """Create a unified provider client."""
        from dipeo.infrastructure.llm.core.types import ProviderType

        # Map provider name to ProviderType
        provider_type_map = {
            LLMServiceName.OPENAI.value: ProviderType.OPENAI,
            LLMServiceName.ANTHROPIC.value: ProviderType.ANTHROPIC,
            LLMServiceName.GOOGLE.value: ProviderType.GOOGLE,
            LLMServiceName.OLLAMA.value: ProviderType.OLLAMA,
            # Claude Code uses Anthropic provider type but special handling
            LLMServiceName.CLAUDE_CODE.value: ProviderType.ANTHROPIC,
        }

        provider_type = provider_type_map.get(provider, ProviderType.OPENAI)

        # Create adapter config
        config = AdapterConfig(
            provider_type=provider_type,
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=self._settings.llm_timeout if hasattr(self._settings, "llm_timeout") else 300,
            max_retries=3,
            retry_delay=1.0,
            retry_backoff=2.0,
        )

        # Import and create the appropriate unified client
        if provider == LLMServiceName.OPENAI.value:
            from dipeo.infrastructure.llm.providers.openai.unified_client import UnifiedOpenAIClient

            return UnifiedOpenAIClient(config)
        elif provider == LLMServiceName.ANTHROPIC.value:
            from dipeo.infrastructure.llm.providers.anthropic.unified_client import (
                UnifiedAnthropicClient,
            )

            return UnifiedAnthropicClient(config)
        elif provider == LLMServiceName.OLLAMA.value:
            # For now, fall back to existing adapter for Ollama
            from dipeo.infrastructure.llm.drivers.factory import create_adapter

            return create_adapter(provider, model, api_key, base_url=base_url, async_mode=True)
        elif provider == LLMServiceName.GOOGLE.value:
            # For now, fall back to existing adapter for Google
            from dipeo.infrastructure.llm.drivers.factory import create_adapter

            return create_adapter(provider, model, api_key, async_mode=True)
        elif provider == LLMServiceName.CLAUDE_CODE.value:
            # Claude Code has special requirements, use existing adapter
            from dipeo.infrastructure.llm.drivers.factory import create_adapter

            return create_adapter(provider, model, api_key, async_mode=True)
        else:
            # Fall back to factory for unknown providers
            from dipeo.infrastructure.llm.drivers.factory import create_adapter

            return create_adapter(provider, model, api_key, base_url=base_url, async_mode=True)

    async def _get_client(self, service: str, model: str, api_key_id: str) -> Any:
        """Get or create a provider client."""
        provider = normalize_service_name(service)

        if provider not in VALID_LLM_SERVICES:
            raise LLMServiceError(service=service, message=f"Unsupported LLM service: {service}")

        cache_key = self._create_cache_key(provider, model, api_key_id)

        # Check cache
        async with self._client_pool_lock:
            if cache_key in self._client_pool:
                entry = self._client_pool[cache_key]
                if time.time() - entry["created_at"] <= 3600:  # 1 hour cache
                    return entry["client"]
                else:
                    del self._client_pool[cache_key]

        # Create new client
        async def create_new_client():
            if provider == LLMServiceName.OLLAMA.value:
                raw_key = ""
                base_url = (
                    self._settings.ollama_host if hasattr(self._settings, "ollama_host") else None
                )
                client = self._create_provider_client(provider, model, raw_key, base_url)
            else:
                raw_key = self._get_api_key(api_key_id)
                client = self._create_provider_client(provider, model, raw_key)

            async with self._client_pool_lock:
                self._client_pool[cache_key] = {
                    "client": client,
                    "created_at": time.time(),
                }

            return client

        return await self._client_cache.get_or_create(
            cache_key, create_new_client, cache_result=False
        )

    def _convert_response_to_chat_result(self, response: LLMResponse) -> ChatResult:
        """Convert LLMResponse to ChatResult."""
        # Extract content as string
        if isinstance(response.content, str):
            content = response.content
        elif hasattr(response.content, "model_dump_json"):
            # Pydantic model
            content = response.content.model_dump_json()
        elif hasattr(response.content, "dict"):
            # Has dict method
            import json

            content = json.dumps(response.content.dict())
        else:
            content = str(response.content)

        # Create ChatResult
        result = ChatResult(text=content)

        # Add token usage if available
        if response.usage:
            result.llm_usage = response.usage

        return result

    async def complete(  # type: ignore[override]
        self, messages: list[dict[str, str]], model: str, api_key_id: str, **kwargs
    ) -> ChatResult:
        """Complete a chat request using the simplified architecture."""
        try:
            if messages is None:
                messages = []

            # Extract execution_phase before processing
            execution_phase = kwargs.pop("execution_phase", None)

            # Determine service provider
            service = kwargs.pop("service", None)
            if service:
                if hasattr(service, "value"):
                    service = service.value
                service = normalize_service_name(str(service))
            else:
                service = self._infer_service_from_model(model)

            # Get or create client
            client = await self._get_client(service, model, api_key_id)

            # Log if enabled
            if hasattr(self, "logger"):
                self.log_debug(f"Using {service} provider for model {model}")
                self.log_debug(f"Messages: {len(messages)}")

            # Prepare kwargs for the client
            client_kwargs = {**kwargs}
            if execution_phase:
                client_kwargs["execution_phase"] = execution_phase

            # Call the client
            if hasattr(client, "async_chat"):
                # Unified client
                response = await client.async_chat(messages=messages, **client_kwargs)
            elif hasattr(client, "chat_async"):
                # Old adapter
                response = await client.chat_async(messages=messages, **client_kwargs)
            else:
                # Sync adapter - run in thread pool
                response = await asyncio.to_thread(client.chat, messages=messages, **client_kwargs)

            # Log response if enabled
            if hasattr(self, "logger") and response:
                if isinstance(response, LLMResponse) or hasattr(response, "content"):
                    response_text = str(response.content)[:50]
                elif hasattr(response, "text"):
                    response_text = str(response.text)[:50]
                else:
                    response_text = str(response)[:50]
                self.log_debug(f"LLM response: {response_text}")

            # Convert response to ChatResult
            if isinstance(response, LLMResponse):
                return self._convert_response_to_chat_result(response)
            elif isinstance(response, ChatResult):
                return response
            else:
                # Handle legacy response formats
                if hasattr(response, "content"):
                    content = response.content
                elif hasattr(response, "text"):
                    content = response.text
                else:
                    content = str(response)

                result = ChatResult(content=content)

                # Try to extract token usage
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
            raise LLMServiceError(service=service, message=str(e)) from e
