from abc import ABC, abstractmethod
from typing import Any

from dipeo_domain import ChatResult, LLMRequestOptions, ToolConfig


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
        # Extract LLMRequestOptions if provided
        options = kwargs.get('options', None)
        if isinstance(options, LLMRequestOptions):
            # Pass tools to the adapter if supported
            if options.tools and self.supports_tools():
                kwargs['tools'] = options.tools
            # Pass other options
            if options.temperature is not None:
                kwargs['temperature'] = options.temperature
            if options.max_tokens is not None:
                kwargs['max_tokens'] = options.max_tokens
            if options.top_p is not None:
                kwargs['top_p'] = options.top_p
            if options.response_format is not None:
                kwargs['response_format'] = options.response_format
        
        return self._make_api_call(messages, **kwargs)
    
    def supports_tools(self) -> bool:
        """Check if this adapter supports tool usage."""
        return False
    
    def supports_response_api(self) -> bool:
        """Check if this adapter supports the new response API."""
        return False
