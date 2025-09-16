"""Google Cloud Vertex AI LLM provider adapter (stub implementation)."""

from typing import Any, AsyncIterator

from dipeo.infrastructure.llm.drivers.types import (
    LLMMessage,
    LLMResponse,
    StreamChunk,
)
from dipeo.infrastructure.llm.drivers.base import BaseLLMAdapter


class VertexAdapter(BaseLLMAdapter):
    """Adapter for Google Cloud Vertex AI LLM provider.
    
    This is a stub implementation that needs to be completed
    with actual Vertex AI API integration.
    """
    
    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        """Initialize Vertex AI adapter.
        
        Args:
            api_key: GCP credentials or API key
            **kwargs: Additional configuration options (project_id, location, etc.)
        """
        super().__init__(api_key=api_key, **kwargs)
        # TODO: Initialize Vertex AI client when implementing
        
    async def complete(
        self,
        messages: list[LLMMessage],
        model: str = "gemini-1.5-pro",
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using Vertex AI.
        
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
            "Google Cloud Vertex AI provider is not yet implemented. "
            "Please use one of the supported providers: "
            "OpenAI, Anthropic, Google, Ollama, or Claude Code."
        )
    
    async def stream(
        self,
        messages: list[LLMMessage],
        model: str = "gemini-1.5-pro",
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion using Vertex AI.
        
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
            "Google Cloud Vertex AI provider is not yet implemented. "
            "Please use one of the supported providers: "
            "OpenAI, Anthropic, Google, Ollama, or Claude Code."
        )
        # Make this an async generator to satisfy type checker
        yield  # type: ignore[unreachable]