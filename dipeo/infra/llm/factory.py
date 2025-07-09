"""Factory for creating LLM adapters."""

from .adapters import ChatGPTAdapter, ClaudeAdapter, GeminiAdapter
from .base import BaseLLMAdapter


def create_adapter(
    provider: str, model_name: str, api_key: str, base_url: str | None = None
) -> BaseLLMAdapter:
    """Factory function to create LLM adapters based on provider.

    Args:
        provider: The LLM provider name ('anthropic', 'openai', 'google', 'xai')
        model_name: The specific model to use
        api_key: API key for the provider
        base_url: Optional custom base URL for the API

    Returns:
        An instance of the appropriate adapter

    Raises:
        ValueError: If the provider is not supported
    """
    provider = provider.lower()

    if provider in ["anthropic", "claude"]:
        return ClaudeAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    if provider in ["openai", "chatgpt"]:
        return ChatGPTAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    if provider in ["google", "gemini"]:
        return GeminiAdapter(model_name=model_name, api_key=api_key)
    raise ValueError(f"Unsupported provider: {provider}")