from abc import ABC, abstractmethod
from typing import Any

from dipeo_domain import ChatResult


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
