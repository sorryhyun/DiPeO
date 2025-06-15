from typing import Optional
from .base import BaseAdapter
from .adapters import ClaudeAdapter, ChatGPTAdapter, GeminiAdapter, GrokAdapter


def create_adapter(
    provider: str,
    model_name: str,
    api_key: str,
    base_url: Optional[str] = None
) -> BaseAdapter:
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
    
    if provider in ['anthropic', 'claude']:
        return ClaudeAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    elif provider in ['openai', 'chatgpt']:
        return ChatGPTAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    elif provider in ['google', 'gemini']:
        return GeminiAdapter(model_name=model_name, api_key=api_key)
    elif provider in ['xai', 'grok']:
        return GrokAdapter(model_name=model_name, api_key=api_key, base_url=base_url)
    else:
        raise ValueError(f"Unsupported provider: {provider}")