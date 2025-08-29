"""Stream chat mixin for LLM adapters."""

from abc import abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from dipeo.diagram_generated import LLMRequestOptions


class StreamChatMixin:
    """Mixin providing streaming chat capabilities."""
    
    @abstractmethod
    async def _stream_chat_impl(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Provider-specific streaming implementation."""
        raise NotImplementedError
    
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat responses token by token with common preprocessing."""
        if messages is None:
            messages = []
        
        # Handle LLMRequestOptions if provided
        options = kwargs.get('options')
        if isinstance(options, LLMRequestOptions):
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
        
        # Delegate to provider-specific implementation
        async for chunk in self._stream_chat_impl(messages, **kwargs):
            yield chunk
    
    def _prepare_streaming_messages(self, messages: list[dict[str, str]]) -> tuple[Any, list[dict]]:
        """Prepare messages for streaming - can be overridden by specific adapters."""
        if hasattr(self, '_extract_system_and_messages'):
            return self._extract_system_and_messages(messages)
        
        # Fallback implementation
        system_prompt = ""
        processed_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            else:
                processed_messages.append({"role": role, "content": content})
        
        return system_prompt, processed_messages