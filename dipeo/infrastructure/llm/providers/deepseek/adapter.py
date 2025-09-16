"""DeepSeek LLM provider adapter (stub implementation)."""

from typing import Any, AsyncIterator

from dipeo.infrastructure.llm.drivers.types import (
    LLMMessage,
    LLMResponse,
    StreamChunk,
)
from dipeo.infrastructure.llm.drivers.base import BaseLLMAdapter


class DeepSeekAdapter(BaseLLMAdapter):
    """Adapter for DeepSeek LLM provider.
    
    This is a stub implementation that needs to be completed
    with actual DeepSeek API integration.
    """
    
    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        """Initialize DeepSeek adapter.
        
        Args:
            api_key: DeepSeek API key
            **kwargs: Additional configuration options
        """
        super().__init__(api_key=api_key, **kwargs)
        # TODO: Initialize DeepSeek client when implementing
        
    async def complete(
        self,
        messages: list[LLMMessage],
        model: str = "deepseek-chat",
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using DeepSeek.
        
        Args:
            messages: List of messages for the conversation
            model: Model to use for generation
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with the generated content
            
        Raises:
            NotImplementedError: This is a stub implementation
        """
        raise NotImplementedError(
            "DeepSeek provider is not yet implemented. "
            "Please use one of the supported providers: "
            "OpenAI, Anthropic, Google, Ollama, or Claude Code."
        )
    
    async def stream(
        self,
        messages: list[LLMMessage],
        model: str = "deepseek-chat",
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion using DeepSeek.
        
        Args:
            messages: List of messages for the conversation
            model: Model to use for generation
            **kwargs: Additional parameters
            
        Yields:
            StreamChunk objects with generated content
            
        Raises:
            NotImplementedError: This is a stub implementation
        """
        raise NotImplementedError(
            "DeepSeek provider is not yet implemented. "
            "Please use one of the supported providers: "
            "OpenAI, Anthropic, Google, Ollama, or Claude Code."
        )
        # Make this an async generator to satisfy type checker
        yield  # type: ignore[unreachable]