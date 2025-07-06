# Barrel exports for llm domain
import warnings
from dipeo_domain import ForgettingMode, LLMService

warnings.warn(
    "Importing from dipeo_infra.external.llm is deprecated. "
    "Use dipeo.infra.adapters.llm instead.",
    DeprecationWarning,
    stacklevel=2
)

from .base import BaseAdapter, ChatResult
from .factory import create_adapter
from .services import LLMInfraService

# Supported models mapping
SUPPORTED_MODELS = {
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "gpt-4-turbo": "openai",
    "gpt-3.5-turbo": "openai",
    "gpt-4.1-nano": "openai",
    "claude-3-5-sonnet-20241022": "anthropic",
    "claude-3-opus-20240229": "anthropic",
    "claude-3-haiku-20240307": "anthropic",
    "gemini-2.0-flash-exp": "google",
    "gemini-1.5-pro": "google",
    "gemini-1.5-flash": "google",
    "grok-2-latest": "xai",
    "grok-2-vision-1212": "xai",
}

__all__ = [
    "SUPPORTED_MODELS",
    "BaseAdapter",
    "ChatResult",
    "ForgettingMode",
    "LLMInfraService",
    "LLMService",
    "create_adapter",
]
