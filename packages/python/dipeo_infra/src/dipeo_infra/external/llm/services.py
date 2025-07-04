import time
from typing import Any

from dipeo_core import APIKeyError, BaseService, LLMServiceError, SupportsLLM
from dipeo_domain import ChatResult
from dipeo_domain import LLMService as LLMServiceEnum
from dipeo_domain.domains.apikey import APIKeyDomainService
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from dipeo_core.constants import VALID_LLM_SERVICES, normalize_service_name

from . import create_adapter


class LLMInfraService(BaseService, SupportsLLM):
    """Service for handling LLM interactions that implements the SupportsLLM protocol."""

    def __init__(self, api_key_service: APIKeyDomainService):
        super().__init__()
        self.api_key_service = api_key_service
        self._adapter_pool: dict[str, dict[str, Any]] = {}

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    async def _call_llm_with_retry(
        self, client: Any, messages: list[dict], **kwargs
    ) -> Any:
        """Internal method for LLM calls with retry logic."""
        return client.chat(messages=messages, **kwargs)

    async def complete(  # type: ignore[override]
        self, messages: list[dict[str, str]], model: str, api_key_id: str, **kwargs
    ) -> ChatResult:
        """Make a call to the specified LLM service with retry logic."""
        try:
            # Infer service from model name
            service = LLMInfraService._infer_service_from_model(model)
            adapter = self._get_client(service, model, api_key_id)

            # Messages should already be in the correct format
            messages_list = messages

            # Pass all kwargs to the adapter
            adapter_kwargs = {**kwargs}

            # Domain ChatResult already has tokenUsage, just return it
            return await self._call_llm_with_retry(
                adapter, messages_list, **adapter_kwargs
            )

        except Exception as e:
            raise LLMServiceError(
                service=LLMInfraService._infer_service_from_model(model),
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

    @staticmethod
    def _infer_service_from_model(model: str) -> str:
        """Infer the service from the model name."""
        # Map model prefixes to services
        if model.startswith("gpt-") or model.startswith("o1-"):
            return "openai"
        if model.startswith("claude-"):
            return "claude"
        if model.startswith("gemini-"):
            return "gemini"
        if model.startswith("grok-"):
            return "grok"
        # Default to openai for backwards compatibility
        return "openai"

    async def get_available_models(self, api_key_id: str) -> list[str]:
        """Get available models for all services based on API key."""
        # For now, return an empty list as we need to know which service
        # the API key is for. This could be enhanced later.
        return []

    async def get_available_models_for_service(
        self, service: str, api_key_id: str
    ) -> list[str]:
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

    def get_token_counts(self, client_name: str, usage: Any) -> Any:
        """Get token counts from usage data.

        This is a pass-through method as token counting is now handled
        by the TokenUsageService in the domain layer.
        """
        return usage
