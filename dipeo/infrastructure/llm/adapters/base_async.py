"""Base async adapter for LLM providers."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from dipeo.diagram_generated import ChatResult, LLMRequestOptions

from ..drivers.base import BaseLLMAdapter


class BaseAsyncLLMAdapter(BaseLLMAdapter, ABC):
    """Base class for async LLM adapters with common async functionality."""
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name, api_key, base_url)
        self._async_client = None
        self._client_lock = None
    
    @abstractmethod
    async def _initialize_async_client(self) -> Any:
        """Initialize the async client for this provider."""
        raise NotImplementedError
    
    @property
    async def async_client(self):
        """Lazy initialization of async client."""
        if self._async_client is None:
            self._async_client = await self._initialize_async_client()
        return self._async_client
    
    @abstractmethod
    async def _make_api_call_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make async API call and return ChatResult."""
        raise NotImplementedError
    
    async def chat_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Async version of chat method with common preprocessing."""
        if messages is None:
            messages = []
        
        # Handle LLMRequestOptions if provided
        options = kwargs.get('options')
        if isinstance(options, LLMRequestOptions):
            if options.tools and self.supports_tools():
                kwargs['tools'] = options.tools
            if options.temperature is not None:
                kwargs['temperature'] = options.temperature
            if options.max_tokens is not None:
                kwargs['max_tokens'] = options.max_tokens
            if options.top_p is not None:
                kwargs['top_p'] = options.top_p
            if options.response_format is not None:
                kwargs['response_format'] = options.response_format
        
        return await self._make_api_call_async(messages, **kwargs)


class BaseStreamingLLMAdapter(BaseAsyncLLMAdapter, ABC):
    """Base class for streaming LLM adapters."""
    
    @abstractmethod
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat responses token by token."""
        raise NotImplementedError
    
    async def _prepare_streaming_messages(self, messages: list[dict[str, str]]) -> tuple[Any, list[dict]]:
        """Prepare messages for streaming - can be overridden by specific adapters."""
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        return system_prompt, processed_messages