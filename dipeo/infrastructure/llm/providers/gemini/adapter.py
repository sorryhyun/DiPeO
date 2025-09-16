"""Google Gemini LLM provider adapter (stub implementation).

Note: Gemini is currently handled by the existing Google provider.
This stub is for future separation if needed.
"""

from typing import Any, AsyncIterator

from dipeo.infrastructure.llm.drivers.types import (
    LLMMessage,
    LLMResponse,
    StreamChunk,
)
from dipeo.infrastructure.llm.drivers.base import BaseLLMAdapter


class GeminiAdapter(BaseLLMAdapter):
    """Adapter for Google Gemini LLM provider.
    
    This is a stub implementation. Currently, Gemini is handled
    by the Google provider implementation.
    """
    
    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        """Initialize Gemini adapter.
        
        Args:
            api_key: Google API key
            **kwargs: Additional configuration options
        """
        super().__init__(api_key=api_key, **kwargs)
        # TODO: Consider if separate implementation is needed
        # Currently handled by Google provider
        
    async def complete(
        self,
        messages: list[LLMMessage],
        model: str = "gemini-1.5-pro",
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using Gemini.
        
        Args:
            messages: List of messages for the conversation
            model: Model to use for generation
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with the generated content
            
        Raises:
            NotImplementedError: Use Google provider for Gemini
        """
        raise NotImplementedError(
            "Gemini is currently supported through the Google provider. "
            "Please use provider='google' with Gemini models."
        )
    
    async def stream(
        self,
        messages: list[LLMMessage],
        model: str = "gemini-1.5-pro",
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion using Gemini.
        
        Args:
            messages: List of messages for the conversation
            model: Model to use for generation
            **kwargs: Additional parameters
            
        Yields:
            StreamChunk objects with generated content
            
        Raises:
            NotImplementedError: Use Google provider for Gemini
        """
        raise NotImplementedError(
            "Gemini is currently supported through the Google provider. "
            "Please use provider='google' with Gemini models."
        )
        # Make this an async generator to satisfy type checker
        yield  # type: ignore[unreachable]