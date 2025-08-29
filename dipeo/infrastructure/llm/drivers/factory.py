"""Factory for creating LLM adapters."""

from typing import Union
from .base import BaseLLMAdapter


def create_adapter(
    provider: str, model_name: str, api_key: str, base_url: str | None = None, async_mode: bool = False
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
    provider = provider.lower()

    if provider in ["anthropic", "claude"]:
        if async_mode:
            from ..adapters.claude_async import ClaudeAsyncAdapter
            return ClaudeAsyncAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
        else:
            from ..adapters.claude import ClaudeAdapter
            return ClaudeAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    
    if provider == "claude-code":
        # Use simplified claude-code adapter
        from ..adapters.claude_code_simplified import ClaudeCodeAdapter
        return ClaudeCodeAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    
    if provider in ["openai", "chatgpt"]:
        if async_mode:
            from ..adapters.openai_async import OpenAIAsyncAdapter
            return OpenAIAsyncAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
        else:
            from ..adapters.openai import ChatGPTAdapter
            return ChatGPTAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    
    if provider in ["google", "gemini"]:
        # For now, keep gemini as is - we can add async version later
        from ..adapters.gemini import GeminiAdapter
        return GeminiAdapter(model_name=model_name, api_key=api_key)
    
    if provider == "ollama":
        # For now, keep ollama as is - we can add async version later
        from ..adapters.ollama import OllamaAdapter
        return OllamaAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    
    raise ValueError(f"Unsupported provider: {provider}")