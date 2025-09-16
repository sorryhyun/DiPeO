"""AWS Bedrock LLM provider adapter (stub implementation)."""

from typing import Any, AsyncIterator

from dipeo.infrastructure.llm.drivers.types import (
    LLMMessage,
    LLMResponse,
    StreamChunk,
)
from dipeo.infrastructure.llm.drivers.base import BaseLLMAdapter


class BedrockAdapter(BaseLLMAdapter):
    """Adapter for AWS Bedrock LLM provider.
    
    This is a stub implementation that needs to be completed
    with actual AWS Bedrock API integration.
    """
    
    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        """Initialize Bedrock adapter.
        
        Args:
            api_key: AWS credentials or access key
            **kwargs: Additional configuration options (region, etc.)
        """
        super().__init__(api_key=api_key, **kwargs)
        # TODO: Initialize AWS Bedrock client when implementing
        
    async def complete(
        self,
        messages: list[LLMMessage],
        model: str = "anthropic.claude-3-5-sonnet",
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using AWS Bedrock.
        
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
            "AWS Bedrock provider is not yet implemented. "
            "Please use one of the supported providers: "
            "OpenAI, Anthropic, Google, Ollama, or Claude Code."
        )
    
    async def stream(
        self,
        messages: list[LLMMessage],
        model: str = "anthropic.claude-3-5-sonnet",
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion using AWS Bedrock.
        
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
            "AWS Bedrock provider is not yet implemented. "
            "Please use one of the supported providers: "
            "OpenAI, Anthropic, Google, Ollama, or Claude Code."
        )
        # Make this an async generator to satisfy type checker
        yield  # type: ignore[unreachable]