"""Factory for creating LLM clients directly."""

from typing import Any

from dipeo.config.services import LLMServiceName, normalize_service_name

from ..core.types import AdapterConfig, ProviderType


def create_adapter(
    provider: str,
    model_name: str,
    api_key: str,
    base_url: str | None = None,
    async_mode: bool = False,
) -> Any:
    """
    Create an LLM client for the specified provider.

    This function returns unified clients directly for all providers.

    Args:
        provider: The LLM provider name
        model_name: The model to use
        api_key: API key for the provider
        base_url: Optional base URL for the provider
        async_mode: If True, returns async adapter; if False, returns sync adapter

    Returns:
        A unified LLM client instance
    """
    provider = normalize_service_name(provider)

    # Create config for all providers
    config = AdapterConfig(
        provider_type=ProviderType.OPENAI,  # Will be overridden below
        model=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    # Return unified clients for all providers
    if provider == LLMServiceName.ANTHROPIC.value:
        # Use unified Anthropic client directly
        from ..providers.anthropic.unified_client import UnifiedAnthropicClient

        config.provider_type = ProviderType.ANTHROPIC
        return UnifiedAnthropicClient(config)

    if provider == LLMServiceName.OPENAI.value:
        # Use unified OpenAI client directly
        from ..providers.openai.unified_client import UnifiedOpenAIClient

        config.provider_type = ProviderType.OPENAI
        return UnifiedOpenAIClient(config)

    if provider == LLMServiceName.CLAUDE_CODE.value:
        # Use unified Claude Code client directly
        from ..providers.claude_code.unified_client import UnifiedClaudeCodeClient

        config.provider_type = ProviderType.ANTHROPIC  # Claude Code uses Anthropic provider type
        return UnifiedClaudeCodeClient(config)

    if provider in [LLMServiceName.GOOGLE.value, LLMServiceName.GEMINI.value]:
        # Use unified Google client directly
        from ..providers.google.unified_client import UnifiedGoogleClient

        config.provider_type = ProviderType.GOOGLE
        return UnifiedGoogleClient(config)

    if provider == LLMServiceName.OLLAMA.value:
        # Use unified Ollama client directly
        from ..providers.ollama.unified_client import UnifiedOllamaClient

        config.provider_type = ProviderType.OLLAMA
        return UnifiedOllamaClient(config)

    raise ValueError(f"Unsupported provider: {provider}")
