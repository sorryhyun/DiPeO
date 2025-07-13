"""Factory for creating LLM adapters."""

from .adapters import ChatGPTAdapter, ClaudeAdapter, GeminiAdapter
from .base import BaseLLMAdapter


def create_adapter(
    provider: str, model_name: str, api_key: str, base_url: str | None = None
) -> BaseLLMAdapter:
    provider = provider.lower()

    if provider in ["anthropic", "claude"]:
        return ClaudeAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    if provider in ["openai", "chatgpt"]:
        return ChatGPTAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    if provider in ["google", "gemini"]:
        return GeminiAdapter(model_name=model_name, api_key=api_key)
    raise ValueError(f"Unsupported provider: {provider}")