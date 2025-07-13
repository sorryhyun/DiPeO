"""LLM infrastructure service implementation."""

import time
from typing import Any, Optional

from dipeo.core import APIKeyError, BaseService, LLMServiceError
from dipeo.core.ports import LLMServicePort
from dipeo.models import ChatResult
from dipeo.models import LLMService as LLMServiceEnum
from dipeo.application.protocols import SupportsAPIKey
from dipeo.domain.llm import LLMDomainService, ModelConfig, RetryStrategy
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from dipeo.core.constants import VALID_LLM_SERVICES, normalize_service_name
from dipeo.infra.config.settings import get_settings

from .factory import create_adapter


class LLMInfraService(BaseService, LLMServicePort):

    def __init__(self, api_key_service: SupportsAPIKey, llm_domain_service: Optional[LLMDomainService] = None):
        super().__init__()
        self.api_key_service = api_key_service
        self._adapter_pool: dict[str, dict[str, Any]] = {}
        self._settings = get_settings()
        self._llm_domain_service = llm_domain_service or LLMDomainService()

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

    def _get_client(self, service: str, model: str, api_key_id: str) -> Any:
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

    async def _call_llm_with_retry(
        self, client: Any, messages: list[dict], **kwargs
    ) -> Any:
        # Try to make the call without retry first
        try:
            return await client.chat(messages=messages, **kwargs)
        except Exception as e:
            # Determine retry strategy using domain service
            retry_strategy = self._llm_domain_service.determine_retry_strategy(e)
            
            if not retry_strategy.should_retry(1):
                raise
            
            # Create retry decorator based on domain-determined strategy
            retry_decorator = retry(
                stop=stop_after_attempt(retry_strategy.max_retries),
                wait=wait_exponential(
                    multiplier=retry_strategy.backoff_factor,
                    min=retry_strategy.initial_delay_seconds,
                    max=retry_strategy.max_delay_seconds
                ),
                retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
            )
            
            @retry_decorator
            async def _make_call():
                return await client.chat(messages=messages, **kwargs)
            
            return await _make_call()

    async def complete(  # type: ignore[override]
        self, messages: list[dict[str, str]], model: str, api_key_id: str, **kwargs
    ) -> ChatResult:
        try:
            if messages is None:
                messages = []
            
            service = LLMInfraService._infer_service_from_model(model)
            
            # Validate model configuration using domain service
            is_valid, error_msg = self._llm_domain_service.validate_model_config(
                provider=service,
                model=model,
                config=kwargs
            )
            if not is_valid:
                raise LLMServiceError(service="llm", message=error_msg)
            
            # Validate prompt size if messages exist
            if messages:
                prompt_text = " ".join(msg.get("content", "") for msg in messages)
                is_valid, error_msg = self._llm_domain_service.validate_prompt_size(
                    prompt=prompt_text,
                    provider=service,
                    model=model
                )
                if not is_valid:
                    self.logger.warning(f"Prompt validation warning: {error_msg}")
            
            adapter = self._get_client(service, model, api_key_id)

            messages_list = messages

            adapter_kwargs = {**kwargs}

            return await self._call_llm_with_retry(
                adapter, messages_list, **adapter_kwargs
            )

        except Exception as e:
            raise LLMServiceError(service="llm", message=str(e))

    @staticmethod
    def _infer_service_from_model(model: str) -> str:
        model_lower = model.lower()
        
        if any(x in model_lower for x in ["gpt", "o1", "o3", "dall-e", "whisper", "embedding"]):
            return "openai"
        elif any(x in model_lower for x in ["claude", "haiku", "sonnet", "opus"]):
            return "anthropic"
        elif any(x in model_lower for x in ["gemini", "bison", "palm"]):
            return "google"
        else:
            return "openai"

    async def get_available_models(self, api_key_id: str) -> list[str]:
        try:
            api_key_data = self.api_key_service.get_api_key(api_key_id)
            service = api_key_data["service"]
            
            if service == "openai":
                try:
                    from openai import OpenAI
                    raw_key = self._get_api_key(api_key_id)
                    client = OpenAI(api_key=raw_key)
                    models_response = client.models.list()
                    
                    chat_models = []
                    for model in models_response.data:
                        model_id = model.id
                        if any(prefix in model_id for prefix in ["gpt-", "o1", "o3", "chatgpt"]):
                            chat_models.append(model_id)
                    
                    if "gpt-4.1-nano" not in chat_models:
                        chat_models.append("gpt-4.1-nano")
                    
                    # Sort models for consistent ordering
                    chat_models.sort(reverse=True)  # Newer models first
                    return chat_models
                    
                except Exception as e:
                    # If API call fails, return empty list
                    self.logger.warning(f"Failed to fetch OpenAI models dynamically: {e}")
                    return []
            elif service == "anthropic":
                # Dynamically fetch models from Anthropic API
                try:
                    import anthropic
                    raw_key = self._get_api_key(api_key_id)
                    client = anthropic.Anthropic(api_key=raw_key)
                    models_response = client.models.list(limit=50)
                    
                    # Extract model IDs from the response
                    model_ids = []
                    for model in models_response.data:
                        model_ids.append(model.id)
                    
                    # Sort models for consistent ordering
                    model_ids.sort(reverse=True)  # Newer models first
                    return model_ids
                    
                except Exception as e:
                    # If API call fails, return empty list
                    self.logger.warning(f"Failed to fetch Anthropic models dynamically: {e}")
                    return []
            elif service == "google":
                # Dynamically fetch models from Google Gemini API
                try:
                    from google import genai
                    raw_key = self._get_api_key(api_key_id)
                    client = genai.Client(api_key=raw_key)
                    
                    # Get models that support generateContent (chat models)
                    chat_models = []
                    for model in client.models.list():
                        if "generateContent" in model.supported_actions:
                            # Extract model name (remove "models/" prefix if present)
                            model_name = model.name
                            if model_name.startswith("models/"):
                                model_name = model_name[7:]  # Remove "models/" prefix
                            chat_models.append(model_name)
                    
                    # Sort models for consistent ordering
                    chat_models.sort(reverse=True)  # Newer models first
                    return chat_models
                    
                except Exception as e:
                    # If API call fails, return empty list
                    self.logger.warning(f"Failed to fetch Google models dynamically: {e}")
                    return []
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