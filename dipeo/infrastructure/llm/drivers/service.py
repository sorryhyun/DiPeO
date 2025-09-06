"""LLM infrastructure service implementation."""

import asyncio
import hashlib
import time
from typing import Any

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from dipeo.config import VALID_LLM_SERVICES, get_settings, normalize_service_name
from dipeo.config.services import LLMServiceName
from dipeo.diagram_generated import ChatResult
from dipeo.domain.base import APIKeyError, LLMServiceError
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin
from dipeo.domain.integrations.ports import APIKeyPort
from dipeo.domain.integrations.ports import LLMService as LLMServicePort
from dipeo.infrastructure.shared.drivers.utils import SingleFlightCache

from .factory import create_adapter


class LLMInfraService(LoggingMixin, InitializationMixin, LLMServicePort):
    def __init__(self, api_key_service: APIKeyPort):
        self.api_key_service = api_key_service
        self._adapter_pool: dict[str, dict[str, Any]] = {}
        self._adapter_pool_lock = asyncio.Lock()
        self._adapter_cache = SingleFlightCache()  # For deduplicating adapter creation
        self._settings = get_settings()

        # Model-specific keywords that help infer the provider
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
            "bison": LLMServiceName.GOOGLE.value,
            "palm": LLMServiceName.GOOGLE.value,
            "llama": LLMServiceName.OLLAMA.value,
            "mistral": LLMServiceName.OLLAMA.value,
            "mixtral": LLMServiceName.OLLAMA.value,
            "gemma": LLMServiceName.OLLAMA.value,
            "phi": LLMServiceName.OLLAMA.value,
            "qwen": LLMServiceName.OLLAMA.value,
            "vicuna": LLMServiceName.OLLAMA.value,
            "orca": LLMServiceName.OLLAMA.value,
            "neural-chat": LLMServiceName.OLLAMA.value,
            "starling": LLMServiceName.OLLAMA.value,
            "codellama": LLMServiceName.OLLAMA.value,
            "deepseek-coder": LLMServiceName.OLLAMA.value,
        }

    async def initialize(self) -> None:
        pass

    def _get_api_key(self, api_key_id: str) -> str:
        try:
            api_key_data = self.api_key_service.get_api_key(api_key_id)
            return api_key_data["key"]
        except APIKeyError as e:
            raise LLMServiceError(
                service="api_key_service", message=f"Failed to get API key: {e}"
            ) from e

    def _create_cache_key(self, provider: str, model: str, api_key_id: str) -> str:
        key_string = f"{provider}:{model}:{api_key_id}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def _get_client(
        self, service: str, model: str, api_key_id: str, async_mode: bool = True
    ) -> Any:
        """
        Get or create an LLM adapter client.

        Args:
            service: The LLM service provider
            model: The model to use
            api_key_id: The API key identifier
            async_mode: If True, creates async adapter; if False, creates sync adapter

        Returns:
            An LLM adapter instance
        """
        provider = normalize_service_name(service)

        if provider not in VALID_LLM_SERVICES:
            raise LLMServiceError(service=service, message=f"Unsupported LLM service: {service}")

        # Include async_mode in cache key to separate sync and async adapters
        cache_key = f"{self._create_cache_key(provider, model, api_key_id)}:{'async' if async_mode else 'sync'}"

        async with self._adapter_pool_lock:
            if cache_key in self._adapter_pool:
                entry = self._adapter_pool[cache_key]
                if time.time() - entry["created_at"] <= 3600:
                    return entry["adapter"]
                else:
                    del self._adapter_pool[cache_key]

        async def create_new_adapter():
            if provider == LLMServiceName.OLLAMA.value:
                raw_key = ""
                base_url = (
                    self._settings.ollama_host if hasattr(self._settings, "ollama_host") else None
                )
                adapter = create_adapter(
                    provider, model, raw_key, base_url=base_url, async_mode=async_mode
                )
            else:
                raw_key = self._get_api_key(api_key_id)
                adapter = create_adapter(provider, model, raw_key, async_mode=async_mode)

            async with self._adapter_pool_lock:
                self._adapter_pool[cache_key] = {
                    "adapter": adapter,
                    "created_at": time.time(),
                }

            return adapter

        return await self._adapter_cache.get_or_create(
            cache_key, create_new_adapter, cache_result=False
        )

    async def _call_llm_with_retry(self, client: Any, messages: list[dict], **kwargs) -> Any:
        """Call LLM with retry logic, handling both sync and async adapters."""
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        ):
            with attempt:
                # Check if this is a new UnifiedAdapter (has async_chat method)
                if hasattr(client, "async_chat"):
                    return await client.async_chat(messages=messages, **kwargs)
                # Check if this is an old async adapter (has chat_async method)
                elif hasattr(client, "chat_async"):
                    return await client.chat_async(messages=messages, **kwargs)
                else:
                    # Sync adapter - run in thread pool
                    return await asyncio.to_thread(client.chat, messages=messages, **kwargs)

    async def complete(  # type: ignore[override]
        self, messages: list[dict[str, str]], model: str, api_key_id: str, **kwargs
    ) -> ChatResult:
        try:
            if messages is None:
                messages = []

            # Extract execution_phase before validation (adapter-specific parameter)
            execution_phase = kwargs.pop("execution_phase", None)

            service = kwargs.pop("service", None)
            if service:
                if hasattr(service, "value"):
                    service = service.value
                service = normalize_service_name(str(service))
            else:
                service = self._infer_service_from_model(model)
            # Validation is now handled by infrastructure adapters
            # The adapters have comprehensive validation in their implementations

            # Always use async adapters for better performance
            adapter = await self._get_client(service, model, api_key_id, async_mode=True)

            messages_list = messages

            adapter_kwargs = {**kwargs}
            # Re-add execution_phase for adapters that support it
            if execution_phase:
                adapter_kwargs["execution_phase"] = execution_phase

            if hasattr(self, "logger"):
                self.log_debug(f"Messages: {len(messages_list)}")
            try:
                result = await self._call_llm_with_retry(adapter, messages_list, **adapter_kwargs)

                if hasattr(self, "logger") and result:
                    # Safely extract response text for logging
                    if isinstance(result, type):
                        # It's a class (like Pydantic model class), not an instance
                        response_text = f"<class {result.__name__}>"
                    elif hasattr(result, "content"):
                        response_text = str(result.content)[:50]
                    elif hasattr(result, "text"):
                        response_text = str(result.text)[:50]
                    else:
                        response_text = str(result)[:50]
                    self.log_debug(f"LLM response: {response_text}")

                # Convert LLMResponse to ChatResult
                # If result is already a ChatResult, return it directly
                if isinstance(result, ChatResult):
                    return result

                # Convert token usage from infrastructure TokenUsage to domain LLMUsage
                llm_usage = None
                if hasattr(result, "usage") and result.usage:
                    # Import the domain LLMUsage model
                    from dipeo.diagram_generated.domain_models import LLMUsage

                    # Convert infrastructure TokenUsage (dataclass) to domain LLMUsage (Pydantic)
                    llm_usage = LLMUsage(
                        input=result.usage.input_tokens,
                        output=result.usage.output_tokens,
                        total=result.usage.total_tokens,
                    )

                # Convert LLMResponse to ChatResult
                chat_result = ChatResult(
                    text=result.content if hasattr(result, "content") else str(result),
                    llm_usage=llm_usage,
                    raw_response=result.raw_response if hasattr(result, "raw_response") else result,
                    tool_outputs=result.tool_outputs if hasattr(result, "tool_outputs") else None,
                )

                # If there's structured output, attach it to the ChatResult
                if hasattr(result, "structured_output"):
                    # Store structured output in raw_response for now
                    # This will be accessible to the decision adapter
                    chat_result.raw_response = result

                return chat_result
            except Exception as inner_e:
                if hasattr(self, "logger"):
                    self.log_error(f"LLM call failed: {type(inner_e).__name__}: {inner_e!s}")
                raise LLMServiceError(
                    service="llm", message=f"LLM service {service} failed: {inner_e!s}"
                ) from inner_e

        except Exception as e:
            raise LLMServiceError(service="llm", message=str(e)) from e

    def _infer_service_from_model(self, model: str) -> str:
        model_lower = model.lower()

        # First try normalize_service_name in case it's a direct service name
        normalized = normalize_service_name(model_lower)
        if normalized in VALID_LLM_SERVICES:
            return normalized

        # Then check for model-specific keywords
        for keyword, provider in self._model_keywords.items():
            if keyword in model_lower:
                return provider

        return LLMServiceName.OPENAI.value

    async def get_available_models(self, api_key_id: str) -> list[str]:
        try:
            api_key_data = self.api_key_service.get_api_key(api_key_id)
            service = api_key_data["service"]
            adapter = await self._get_client(service, "dummy", api_key_id)

            return await adapter.get_available_models()

        except Exception as e:
            raise LLMServiceError(
                service="llm", message=f"Failed to get available models: {e}"
            ) from e

    def get_token_counts(self, client_name: str, usage: Any) -> Any:
        """Extract token usage information from provider response."""
        if hasattr(usage, "tokenUsage"):
            return usage.tokenUsage
        elif hasattr(usage, "token_usage"):
            return usage.token_usage
        else:
            return None

    async def validate_api_key(self, api_key_id: str, provider: str | None = None) -> bool:
        """Validate an API key is functional."""
        try:
            # Try a minimal completion to validate the key
            model = (
                "gpt-5-nano-2025-08-07"
                if not provider
                else self._get_default_model_for_provider(provider)
            )
            await self.complete(
                messages=[{"role": "user", "content": "test"}],
                model=model,
                api_key_id=api_key_id,
                max_tokens=1,
            )
            return True
        except Exception:
            return False

    async def get_provider_for_model(self, model: str) -> str | None:
        """Determine which provider supports a given model."""
        return self._infer_service_from_model(model)

    def _get_default_model_for_provider(self, provider: str) -> str:
        """Get a default model for a provider."""
        provider = normalize_service_name(provider)
        if provider == LLMServiceName.OPENAI.value:
            return "gpt-5-nano-2025-08-07"
        elif (
            provider == LLMServiceName.ANTHROPIC.value
            or provider == LLMServiceName.CLAUDE_CODE.value
        ):
            return "claude-3-5-sonnet-20241022"
        elif provider in [LLMServiceName.GOOGLE.value, LLMServiceName.GEMINI.value]:
            return "gemini-1.5-pro"
        elif provider == LLMServiceName.OLLAMA.value:
            return "llama3"
        else:
            return "gpt-5-nano-2025-08-07"
