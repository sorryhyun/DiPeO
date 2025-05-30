from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class ChatResult:
    """Unified result type for all LLM adapters."""
    text: str
    usage: Optional[Any] = None  # Provider-specific usage object
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    raw_response: Optional[Any] = None  # Original provider response


class BaseAdapter:
    """Base interface for LLM adapters."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def chat(self, system_prompt: str, cacheable_prompt: str = '', user_prompt: str = '', citation_target: str = '',
             **kwargs) -> ChatResult:  # noqa: E501
        raise NotImplementedError

    def list_models(self) -> list[str]:
        """List available models for this provider."""
        raise NotImplementedError