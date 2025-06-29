import time
from typing import Any

from dipeo_core import APIKeyError, BaseService, LLMServiceError, SupportsLLM
from dipeo_domain import LLMService as LLMServiceEnum
from dipeo_domain import TokenUsage
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from dipeo_server.domains.apikey import APIKeyDomainService
from dipeo_server.shared.constants import VALID_LLM_SERVICES, normalize_service_name

from . import ChatResult, create_adapter
from .token_usage_service import TokenUsageService


class LLMService(BaseService, SupportsLLM):
    """Service for handling LLM interactions that implements the SupportsLLM protocol."""

    def __init__(self, api_key_service: APIKeyDomainService):
        super().__init__()
        self.api_key_service = api_key_service
        self._adapter_pool = {}

    async def initialize(self) -> None:
        """Initialize the LLM service."""
        # No specific initialization needed for now
        pass

    def _get_api_key(self, api_key_id: str) -> str:
        """Get raw API key from service."""
        try:
            api_key_data = self.api_key_service.get_api_key(api_key_id)
            return api_key_data["key"]
        except APIKeyError as e:
            raise LLMServiceError(
                service="api_key_service", message=f"Failed to get API key: {e}"
            )

    def _get_client(self, service: str, model: str, api_key_id: str) -> Any:
        """Get the appropriate LLM adapter with connection pooling and TTL."""
        provider = normalize_service_name(service)

        if provider not in VALID_LLM_SERVICES:
            raise LLMServiceError(
                service=service, message=f"Unsupported LLM service: {service}"
            )

        cache_key = f"{provider}:{model}:{api_key_id}"

        if cache_key not in self._adapter_pool:
            raw_key = self._get_api_key(api_key_id)

            self._adapter_pool[cache_key] = {
                "adapter": create_adapter(provider, model, raw_key),
                "created_at": time.time(),
            }

        entry = self._adapter_pool[cache_key]
        if time.time() - entry["created_at"] > 3600:
            del self._adapter_pool[cache_key]
            return self._get_client(service, model, api_key_id)

        return entry["adapter"]

    def get_token_counts(self, client_name: str, usage: Any) -> TokenUsage:
        """Get token counts from LLM usage."""
        normalized_service = normalize_service_name(client_name)
        return TokenUsageService.from_usage(usage, normalized_service)

    def _extract_result_and_usage(self, result: Any) -> tuple[str, Any]:
        """Extract text and usage from adapter result."""
        if isinstance(result, ChatResult):
            return result.text, result.usage
        return result or "", None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    async def _call_llm_with_retry(
        self, client: Any, system_prompt: str, user_prompt: str
    ) -> Any:
        """Internal method for LLM calls with retry logic."""
        return client.chat(system_prompt=system_prompt, user_prompt=user_prompt)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    async def _call_llm_with_messages_retry(
        self, client: Any, messages: list[dict]
    ) -> Any:
        """Internal method for LLM calls with messages array and retry logic."""
        return client.chat_with_messages(messages=messages)

    async def call_llm(
        self,
        service: str | None,
        api_key_id: str,
        model: str,
        messages: str | list[dict],
        system_prompt: str = "",
    ) -> dict[str, str | float]:
        """Make a call to the specified LLM service with retry logic."""
        try:
            adapter = self._get_client(service or "chatgpt", model, api_key_id)

            if isinstance(messages, list):
                result = await self._call_llm_with_messages_retry(adapter, messages)
            else:
                result = await self._call_llm_with_retry(
                    adapter, system_prompt, messages
                )

            text, usage = self._extract_result_and_usage(result)
            token_usage = self.get_token_counts(service or "chatgpt", usage)
            return {"response": text, "token_usage": token_usage}

        except Exception as e:
            raise LLMServiceError(
                service=service or "chatgpt",
                message=f"LLM call failed: {e}",
                model=model,
            )

    def pre_initialize_model(self, service: str, model: str, api_key_id: str) -> bool:
        """Pre-initialize a model client for faster subsequent use."""
        try:
            self._get_client(service, model, api_key_id)
            return True
        except Exception as e:
            raise LLMServiceError(
                service=service,
                message=f"Failed to pre-initialize model: {e}",
                model=model,
            )

    async def get_available_models(self, service: str, api_key_id: str) -> list[str]:
        """Get available models for a service."""
        raw_key = self._get_api_key(api_key_id)
        normalized_service = normalize_service_name(service)

        if normalized_service == LLMServiceEnum.openai.value:
            try:
                import openai

                client = openai.OpenAI(api_key=raw_key)
                return [model.id for model in client.models.list()]
            except Exception as e:
                raise LLMServiceError(
                    service=normalized_service,
                    message=f"Failed to fetch OpenAI models: {e}",
                )

        return []
