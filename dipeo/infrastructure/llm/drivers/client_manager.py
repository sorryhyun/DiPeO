"""Client pool and creation management for LLM services."""

import asyncio
import hashlib
import time
from typing import Any

from dipeo.config import VALID_LLM_SERVICES, get_settings, normalize_service_name
from dipeo.config.services import LLMServiceName
from dipeo.domain.base import APIKeyError, LLMServiceError
from dipeo.domain.base.mixins import LoggingMixin
from dipeo.domain.integrations.ports import APIKeyPort
from dipeo.infrastructure.common.utils import SingleFlightCache
from dipeo.infrastructure.llm.drivers.types import AdapterConfig


class ClientManager(LoggingMixin):
    """Manages LLM client pool, caching, and creation."""

    def __init__(self, api_key_service: APIKeyPort):
        super().__init__()
        self.api_key_service = api_key_service
        self._client_pool: dict[str, dict[str, Any]] = {}
        self._client_pool_lock = asyncio.Lock()
        self._client_cache = SingleFlightCache()
        self._settings = get_settings()

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

    def _create_provider_client(
        self, provider: str, model: str, api_key: str, base_url: str | None = None
    ) -> Any:
        from dipeo.infrastructure.llm.drivers.types import ProviderType

        provider_type_map = {
            LLMServiceName.OPENAI.value: ProviderType.OPENAI,
            LLMServiceName.ANTHROPIC.value: ProviderType.ANTHROPIC,
            LLMServiceName.GOOGLE.value: ProviderType.GOOGLE,
            LLMServiceName.OLLAMA.value: ProviderType.OLLAMA,
            LLMServiceName.CLAUDE_CODE.value: ProviderType.CLAUDE_CODE,
            LLMServiceName.CLAUDE_CODE_CUSTOM.value: ProviderType.CLAUDE_CODE,
        }

        provider_type = provider_type_map.get(provider, ProviderType.OPENAI)

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

        if provider == LLMServiceName.OPENAI.value:
            from dipeo.infrastructure.llm.providers.openai.unified_client import UnifiedOpenAIClient

            return UnifiedOpenAIClient(config)
        elif provider == LLMServiceName.ANTHROPIC.value:
            from dipeo.infrastructure.llm.providers.anthropic.unified_client import (
                UnifiedAnthropicClient,
            )

            return UnifiedAnthropicClient(config)
        elif provider == LLMServiceName.OLLAMA.value:
            from dipeo.infrastructure.llm.drivers.factory import create_adapter

            return create_adapter(provider, model, api_key, base_url=base_url, async_mode=True)
        elif (
            provider == LLMServiceName.GOOGLE.value
            or provider == LLMServiceName.CLAUDE_CODE.value
            or provider == LLMServiceName.CLAUDE_CODE_CUSTOM.value
        ):
            from dipeo.infrastructure.llm.drivers.factory import create_adapter

            return create_adapter(provider, model, api_key, async_mode=True)
        else:
            from dipeo.infrastructure.llm.drivers.factory import create_adapter

            return create_adapter(provider, model, api_key, base_url=base_url, async_mode=True)

    async def get_client(self, service_name: str, model: str, api_key_id: str) -> Any:
        """Get or create a client for the specified service and model."""
        provider = normalize_service_name(service_name)

        if provider not in VALID_LLM_SERVICES:
            raise LLMServiceError(
                service=service_name, message=f"Unsupported LLM service: {service_name}"
            )

        cache_key = self._create_cache_key(provider, model, api_key_id)

        async with self._client_pool_lock:
            if cache_key in self._client_pool:
                entry = self._client_pool[cache_key]
                if time.time() - entry["created_at"] <= 3600:
                    return entry["client"]
                else:
                    del self._client_pool[cache_key]

        async def create_new_client():
            if provider == LLMServiceName.OLLAMA.value:
                raw_key = ""
                base_url = (
                    self._settings.ollama_host if hasattr(self._settings, "ollama_host") else None
                )
                client = self._create_provider_client(provider, model, raw_key, base_url)
            elif provider in [
                LLMServiceName.CLAUDE_CODE.value,
                LLMServiceName.CLAUDE_CODE_CUSTOM.value,
            ]:
                raw_key = ""
                client = self._create_provider_client(provider, model, raw_key)
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
