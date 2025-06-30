from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ChatResult:
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    raw_response: Any | None = None

    @property
    def has_usage(self) -> bool:
        return any(
            v is not None
            for v in (self.prompt_tokens, self.completion_tokens, self.total_tokens)
        )

    @property
    def usage(self) -> dict[str, int | None] | None:
        if self.has_usage:
            return {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            }
        return None


class BaseAdapter(ABC):
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = self._initialize_client()

    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the provider-specific client."""
        raise NotImplementedError

    @abstractmethod
    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make API call and return ChatResult. Each adapter implements this."""
        raise NotImplementedError

    def chat(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Main chat method - delegates to _make_api_call."""
        return self._make_api_call(messages, **kwargs)
