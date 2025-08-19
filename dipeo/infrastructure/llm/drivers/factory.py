"""Factory for creating LLM adapters."""

from .base import BaseLLMAdapter


def create_adapter(
    provider: str, model_name: str, api_key: str, base_url: str | None = None
) -> BaseLLMAdapter:
    provider = provider.lower()

    if provider in ["anthropic", "claude"]:
        from ..adapters.claude import ClaudeAdapter
        return ClaudeAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    if provider == "claude-code":
        from ..adapters.claude_code import ClaudeCodeAdapter
        return ClaudeCodeAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    if provider in ["openai", "chatgpt"]:
        from ..adapters.openai import ChatGPTAdapter
        return ChatGPTAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    if provider in ["google", "gemini"]:
        from ..adapters.gemini import GeminiAdapter
        return GeminiAdapter(model_name=model_name, api_key=api_key)
    if provider == "ollama":
        from ..adapters.ollama import OllamaAdapter
        return OllamaAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    raise ValueError(f"Unsupported provider: {provider}")