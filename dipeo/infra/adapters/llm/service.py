"""LLM infrastructure service implementation."""

import time
from typing import Any

from dipeo.core import APIKeyError, BaseService, LLMServiceError
from dipeo.core.ports import LLMServicePort
from dipeo.domain import ChatResult
from dipeo.domain import LLMService as LLMServiceEnum
from dipeo.domain.domains.apikey import APIKeyDomainService
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from dipeo.core.constants import VALID_LLM_SERVICES, normalize_service_name

from .factory import create_adapter


class LLMInfraService(BaseService, LLMServicePort):
    """Service for handling LLM interactions that implements the LLMServicePort protocol."""

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
            raise LLMServiceError(service="llm", message=str(e))

    @staticmethod
    def _infer_service_from_model(model: str) -> str:
        """Infer the LLM service from the model name."""
        model_lower = model.lower()
        
        # OpenAI models
        if any(x in model_lower for x in ["gpt", "o1", "o3", "dall-e", "whisper", "embedding"]):
            return "openai"
        # Claude models
        elif any(x in model_lower for x in ["claude", "haiku", "sonnet", "opus"]):
            return "anthropic"
        # Gemini models
        elif any(x in model_lower for x in ["gemini", "bison", "palm"]):
            return "google"
        # Grok models
        elif "grok" in model_lower:
            return "xai"
        else:
            # Default to OpenAI for unknown models
            return "openai"

    async def get_available_models(self, api_key_id: str) -> list[str]:
        """Get list of available models for the given API key."""
        try:
            api_key_data = self.api_key_service.get_api_key(api_key_id)
            service = api_key_data["service"]
            
            # Return a static list of models based on the service
            # In a real implementation, this could query the provider's API
            if service == "openai":
                return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4.1-nano"]
            elif service == "anthropic":
                return ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-2.1"]
            elif service == "google":
                return ["gemini-pro", "gemini-pro-vision"]
            elif service == "xai":
                return ["grok-1", "grok-2"]
            else:
                return []
        except Exception as e:
            raise LLMServiceError(
                service="llm", message=f"Failed to get available models: {e}"
            )

    def get_token_counts(self, client_name: str, usage: Any) -> Any:
        """Extract token usage information from provider response.
        
        This is typically handled by the adapters themselves,
        but this method provides a consistent interface.
        """
        # The adapters already return ChatResult with TokenUsage
        # This method is here for compatibility with the protocol
        if hasattr(usage, 'tokenUsage'):
            return usage.tokenUsage
        elif hasattr(usage, 'token_usage'):
            return usage.token_usage
        else:
            return None