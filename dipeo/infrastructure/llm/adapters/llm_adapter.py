"""Adapters that bridge existing LLM infrastructure to new domain ports."""

from typing import Any, Optional

from dipeo.domain.llm.ports import LLMService as LLMServicePort
from dipeo.diagram_generated import ChatResult, TokenUsage
from dipeo.domain.llm import LLMClient, LLMService
from dipeo.infrastructure.llm.drivers.service import LLMInfraService


class LLMClientAdapter(LLMClient):
    """Adapter wrapping LLMInfraService to implement domain LLMClient port."""

    def __init__(self, llm_service: LLMServicePort | None = None):
        self._service = llm_service
        if not self._service:
            # Initialize with minimal dependencies for standalone use
            from dipeo.domain.integrations.ports import APIKeyPort
            from dipeo.infrastructure.shared.keys.drivers.environment_service import EnvironmentAPIKeyService
            api_key_service = EnvironmentAPIKeyService()
            self._service = LLMInfraService(api_key_service)

    async def initialize(self) -> None:
        """Initialize the service."""
        if hasattr(self._service, 'initialize'):
            await self._service.initialize()

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        api_key_id: str,
        **kwargs,
    ) -> ChatResult:
        """Complete a chat prompt using the underlying service."""
        return await self._service.complete(
            messages=messages,
            model=model,
            api_key_id=api_key_id,
            **kwargs,
        )


    async def get_available_models(self, api_key_id: str) -> list[str]:
        """Get available models for the provider."""
        # This would need implementation in the underlying service
        # For now, return a default list based on provider
        return [
            "gpt-5-nano-2025-08-07",
            "gpt-4o",
            "gpt-4o-mini",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-latest",
        ]

    def get_token_counts(
        self, client_name: str, usage: Any
    ) -> TokenUsage:
        """Extract token usage from provider response."""
        if hasattr(self._service, 'get_token_counts'):
            raw_usage = self._service.get_token_counts(client_name, usage)
            if raw_usage:
                # Convert raw usage to TokenUsage if needed
                if isinstance(raw_usage, TokenUsage):
                    return raw_usage
                elif isinstance(raw_usage, dict):
                    return TokenUsage(
                        input=raw_usage.get('input_tokens', raw_usage.get('prompt_tokens', 0)),
                        output=raw_usage.get('output_tokens', raw_usage.get('completion_tokens', 0)),
                        cached=raw_usage.get('cached_tokens'),
                        total=raw_usage.get('total_tokens', 0),
                    )
                elif hasattr(raw_usage, 'input'):
                    return raw_usage
        
        # Default implementation
        if isinstance(usage, dict):
            return TokenUsage(
                input=usage.get('input_tokens', usage.get('prompt_tokens', 0)),
                output=usage.get('output_tokens', usage.get('completion_tokens', 0)),
                cached=usage.get('cached_tokens'),
                total=usage.get('total_tokens', 0),
            )
        return TokenUsage(input=0, output=0, cached=None, total=0)


class LLMServiceAdapter(LLMService):
    """High-level LLM service adapter implementing domain LLMService port."""

    def __init__(self, llm_service: LLMServicePort | None = None):
        self._service = llm_service
        if not self._service:
            from dipeo.infrastructure.shared.keys.drivers.environment_service import EnvironmentAPIKeyService
            api_key_service = EnvironmentAPIKeyService()
            self._service = LLMInfraService(api_key_service)

    async def complete(
        self,
        messages: list[dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key_id: Optional[str] = None,
        **kwargs,
    ) -> ChatResult:
        """Complete with automatic provider selection."""
        # Determine model if not provided
        if not model:
            model = "gpt-5-nano-2025-08-07"  # Default model
        
        # Let the service determine the provider from the model
        return await self._service.complete(
            messages=messages,
            model=model,
            api_key_id=api_key_id or "default",
            **kwargs,
        )


    async def validate_api_key(
        self, api_key_id: str, provider: Optional[str] = None
    ) -> bool:
        """Validate an API key is functional."""
        try:
            # Try a minimal completion to validate the key
            await self._service.chat(
                messages=[{"role": "user", "content": "test"}],
                model="gpt-5-nano-2025-08-07" if not provider else f"{provider}-test",
                api_key_id=api_key_id,
                max_tokens=1,
            )
            return True
        except Exception:
            return False

    async def get_provider_for_model(self, model: str) -> Optional[str]:
        """Determine which provider supports a given model."""
        # Map models to providers
        if model.startswith("gpt") or model.startswith("o1") or model.startswith("o3"):
            return "openai"
        elif "claude" in model:
            return "anthropic"
        elif "gemini" in model or "bison" in model:
            return "google"
        elif model in ["llama", "mistral", "mixtral", "codellama"]:
            return "ollama"
        return None


