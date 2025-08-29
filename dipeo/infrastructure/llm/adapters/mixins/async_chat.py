"""Async chat mixin for LLM adapters."""

import asyncio
from abc import abstractmethod
from typing import Any

from dipeo.diagram_generated import ChatResult, LLMRequestOptions


class AsyncChatMixin:
    """Mixin providing async chat capabilities."""
    
    def __init__(self):
        self._async_client = None
        self._client_lock = None
    
    @abstractmethod
    async def _initialize_async_client(self) -> Any:
        """Initialize the async client for this provider."""
        raise NotImplementedError
    
    @abstractmethod
    async def _make_api_call_async_impl(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Provider-specific async API call implementation."""
        raise NotImplementedError
    
    async def get_async_client(self) -> Any:
        """Get or create async client with thread-safe initialization."""
        if self._async_client is None:
            if self._client_lock is None:
                self._client_lock = asyncio.Lock()
            
            async with self._client_lock:
                if self._async_client is None:
                    self._async_client = await self._initialize_async_client()
        
        return self._async_client
    
    async def chat_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Async version of chat method with common preprocessing."""
        if messages is None:
            messages = []
        
        # Handle LLMRequestOptions if provided
        options = kwargs.get('options')
        if isinstance(options, LLMRequestOptions):
            # Ensure we have access to supports_tools method from base class
            if hasattr(self, 'supports_tools') and self.supports_tools():
                if options.tools:
                    kwargs['tools'] = options.tools
            if options.temperature is not None:
                kwargs['temperature'] = options.temperature
            if options.max_tokens is not None:
                kwargs['max_tokens'] = options.max_tokens
            if options.top_p is not None:
                kwargs['top_p'] = options.top_p
            if options.response_format is not None:
                kwargs['response_format'] = options.response_format
        
        return await self._make_api_call_async_impl(messages, **kwargs)