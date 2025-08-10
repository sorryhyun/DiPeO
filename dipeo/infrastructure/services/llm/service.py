"""LLM infrastructure service implementation."""

import asyncio
import hashlib
import logging
import time
from typing import Any

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from dipeo.core import APIKeyError, BaseService, LLMServiceError
from dipeo.core.constants import VALID_LLM_SERVICES, normalize_service_name
from dipeo.core.ports import LLMServicePort
from dipeo.core.ports.apikey_port import APIKeyPort
from dipeo.domain.llm import LLMDomainService
from dipeo.infrastructure.config import get_settings
from dipeo.infrastructure.utils.single_flight_cache import SingleFlightCache
from dipeo.diagram_generated import ChatResult

from .factory import create_adapter


class LLMInfraService(BaseService, LLMServicePort):

    def __init__(self, api_key_service: APIKeyPort, llm_domain_service: LLMDomainService | None = None):
        super().__init__()
        self.api_key_service = api_key_service
        self._adapter_pool: dict[str, dict[str, Any]] = {}
        self._adapter_pool_lock = asyncio.Lock()
        self._adapter_cache = SingleFlightCache()  # For deduplicating adapter creation
        self._settings = get_settings()
        self._llm_domain_service = llm_domain_service or LLMDomainService()
        self.logger = logging.getLogger(__name__)
        self._provider_mapping = {
            "gpt": "openai",
            "o1": "openai",
            "o3": "openai",
            "dall-e": "openai",
            "whisper": "openai",
            "embedding": "openai",
            "claude": "anthropic",
            "haiku": "anthropic",
            "sonnet": "anthropic",
            "opus": "anthropic",
            "gemini": "google",
            "bison": "google",
            "palm": "google",
            "llama": "ollama",
            "mistral": "ollama",
            "mixtral": "ollama",
            "gemma": "ollama",
            "phi": "ollama",
            "qwen": "ollama",
            "vicuna": "ollama",
            "orca": "ollama",
            "neural-chat": "ollama",
            "starling": "ollama",
            "codellama": "ollama",
            "deepseek-coder": "ollama"
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
            )

    def _create_cache_key(self, provider: str, model: str, api_key_id: str) -> str:
        key_string = f"{provider}:{model}:{api_key_id}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def _get_client(self, service: str, model: str, api_key_id: str) -> Any:
        provider = normalize_service_name(service)

        if provider not in VALID_LLM_SERVICES:
            raise LLMServiceError(
                service=service, message=f"Unsupported LLM service: {service}"
            )

        cache_key = self._create_cache_key(provider, model, api_key_id)

        async with self._adapter_pool_lock:
            if cache_key in self._adapter_pool:
                entry = self._adapter_pool[cache_key]
                if time.time() - entry["created_at"] <= 3600:
                    return entry["adapter"]
                else:
                    del self._adapter_pool[cache_key]
        async def create_new_adapter():
            if provider == "ollama":
                raw_key = ""
                base_url = self._settings.ollama_host if hasattr(self._settings, 'ollama_host') else None
                adapter = create_adapter(provider, model, raw_key, base_url=base_url)
            else:
                raw_key = self._get_api_key(api_key_id)
                adapter = create_adapter(provider, model, raw_key)
            
            async with self._adapter_pool_lock:
                self._adapter_pool[cache_key] = {
                    "adapter": adapter,
                    "created_at": time.time(),
                }
            
            return adapter
        return await self._adapter_cache.get_or_create(
            cache_key,
            create_new_adapter,
            cache_result=False
        )

    async def _call_llm_with_retry(
        self, client: Any, messages: list[dict], **kwargs
    ) -> Any:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        ):
            with attempt:
                if hasattr(client, 'chat_async'):
                    return await client.chat_async(messages=messages, **kwargs)
                else:
                    return await asyncio.to_thread(client.chat, messages=messages, **kwargs)

    async def complete(  # type: ignore[override]
        self, messages: list[dict[str, str]], model: str, api_key_id: str, **kwargs
    ) -> ChatResult:
        try:
            if messages is None:
                messages = []
            
            service = kwargs.pop('service', None)
            if service:
                if hasattr(service, 'value'):
                    service = service.value
                service = normalize_service_name(str(service))
            else:
                service = self._infer_service_from_model(model)
            is_valid, error_msg = self._llm_domain_service.validate_model_config(
                provider=service,
                model=model,
                config=kwargs
            )
            if not is_valid:
                raise LLMServiceError(service="llm", message=error_msg)
            if messages:
                prompt_text = " ".join(msg.get("content", "") for msg in messages)
                is_valid, error_msg = self._llm_domain_service.validate_prompt_size(
                    prompt=prompt_text,
                    provider=service,
                    model=model
                )
                if not is_valid and hasattr(self, 'logger'):
                    self.logger.warning(f"Prompt validation warning: {error_msg}")
            
            adapter = await self._get_client(service, model, api_key_id)

            messages_list = messages

            adapter_kwargs = {**kwargs}
            
            if hasattr(self, 'logger'):
                self.logger.debug(f"Messages: {len(messages_list)}")

            try:
                result = await self._call_llm_with_retry(
                    adapter, messages_list, **adapter_kwargs
                )
                
                if hasattr(self, 'logger') and result:
                    response_text = getattr(result, 'text', str(result))[:50]
                    self.logger.debug(f"LLM response: {response_text}")
                
                return result
            except Exception as inner_e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"LLM call failed: {type(inner_e).__name__}: {inner_e!s}")
                raise LLMServiceError(service="llm", message=f"LLM service {service} failed: {inner_e!s}")

        except Exception as e:
            raise LLMServiceError(service="llm", message=str(e))

    def _infer_service_from_model(self, model: str) -> str:
        model_lower = model.lower()
        
        for keyword, provider in self._provider_mapping.items():
            if keyword in model_lower:
                return provider
        
        return "openai"

    async def get_available_models(self, api_key_id: str) -> list[str]:
        try:
            api_key_data = self.api_key_service.get_api_key(api_key_id)
            service = api_key_data["service"]
            adapter = await self._get_client(service, "dummy", api_key_id)
            
            return await adapter.get_available_models()
            
        except Exception as e:
            raise LLMServiceError(
                service="llm", message=f"Failed to get available models: {e}"
            )

    def get_token_counts(self, client_name: str, usage: Any) -> Any:
        """Extract token usage information from provider response."""
        if hasattr(usage, 'tokenUsage'):
            return usage.tokenUsage
        elif hasattr(usage, 'token_usage'):
            return usage.token_usage
        else:
            return None