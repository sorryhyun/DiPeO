"""Factory for creating LLM adapters."""

from dipeo.config.services import LLMServiceName, normalize_service_name

from ..core.types import AdapterConfig, ProviderType
from .base import BaseLLMAdapter


def create_adapter(
    provider: str,
    model_name: str,
    api_key: str,
    base_url: str | None = None,
    async_mode: bool = False,
) -> BaseLLMAdapter:
    """
    Create an LLM adapter for the specified provider.

    Args:
        provider: The LLM provider name
        model_name: The model to use
        api_key: API key for the provider
        base_url: Optional base URL for the provider
        async_mode: If True, returns async adapter; if False, returns sync adapter

    Returns:
        An LLM adapter instance (sync or async based on async_mode)
    """
    provider = normalize_service_name(provider)

    # Use new refactored providers when available
    if provider == LLMServiceName.ANTHROPIC.value:
        # Use new refactored Anthropic provider
        from ..providers.anthropic import AnthropicAdapter

        config = AdapterConfig(
            provider_type=ProviderType.ANTHROPIC,
            model=model_name,
            api_key=api_key,
            base_url=base_url,
        )
        adapter = AnthropicAdapter(config)
        adapter.model = model_name
        return adapter

    if provider == LLMServiceName.CLAUDE_CODE.value:
        # Use new separated Claude Code provider
        from ..providers.claude_code import ClaudeCodeAdapter

        config = AdapterConfig(
            provider_type=ProviderType.ANTHROPIC,  # Claude Code uses Anthropic provider type
            model=model_name,
            api_key=api_key,
            base_url=base_url,
        )
        adapter = ClaudeCodeAdapter(config)
        adapter.model = model_name
        return adapter

    if provider == LLMServiceName.OPENAI.value:
        # Use new refactored OpenAI provider
        from ..providers.openai import OpenAIAdapter

        config = AdapterConfig(
            provider_type=ProviderType.OPENAI,
            model=model_name,
            api_key=api_key,
            base_url=base_url,
        )
        adapter = OpenAIAdapter(config)
        adapter.model = model_name
        return adapter

    if provider in [LLMServiceName.GOOGLE.value, LLMServiceName.GEMINI.value]:
        # Use new refactored Google provider
        from ..providers.google import GoogleAdapter

        config = AdapterConfig(
            provider_type=ProviderType.GOOGLE,
            model=model_name,
            api_key=api_key,
            base_url=base_url,
        )
        adapter = GoogleAdapter(config)
        adapter.model = model_name
        return adapter

    if provider == LLMServiceName.OLLAMA.value:
        # Use new refactored Ollama provider
        from ..providers.ollama import OllamaAdapter

        config = AdapterConfig(
            provider_type=ProviderType.OLLAMA,
            model=model_name,
            api_key=api_key,
            base_url=base_url,
        )
        adapter = OllamaAdapter(config)
        adapter.model = model_name
        return adapter

    raise ValueError(f"Unsupported provider: {provider}")
