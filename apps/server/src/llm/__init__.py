from .base import BaseAdapter, ChatResult
from .factory import create_adapter

# Supported models mapping
SUPPORTED_MODELS = {
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "gpt-4-turbo": "openai",
    "gpt-3.5-turbo": "openai",
    "claude-3-5-sonnet-20241022": "anthropic",
    "claude-3-opus-20240229": "anthropic",
    "claude-3-haiku-20240307": "anthropic",
    "gemini-2.0-flash-exp": "google",
    "gemini-1.5-pro": "google",
    "gemini-1.5-flash": "google",
    "grok-2-latest": "xai",
    "grok-2-vision-1212": "xai"
}

__all__ = ['BaseAdapter', 'ChatResult', 'create_adapter', 'SUPPORTED_MODELS']