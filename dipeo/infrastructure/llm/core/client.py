"""Client abstraction protocols for LLM providers."""

from collections.abc import AsyncIterator, Iterator
from typing import Any, Protocol, runtime_checkable

from dipeo.config.llm import DEFAULT_TEMPERATURE

from .types import AdapterConfig, LLMResponse


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for synchronous LLM client operations."""

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute a chat completion request."""
        ...

    def stream_chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Stream a chat completion response."""
        ...

    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens in text for a specific model."""
        ...

    def validate_connection(self) -> bool:
        """Validate client connection and credentials."""
        ...


@runtime_checkable
class AsyncLLMClient(Protocol):
    """Protocol for asynchronous LLM client operations."""

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute an async chat completion request."""
        ...

    async def stream_chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream an async chat completion response."""
        ...

    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens in text for a specific model."""
        ...

    async def validate_connection(self) -> bool:
        """Validate client connection and credentials."""
        ...


class BaseClientWrapper:
    """Base class for client wrappers."""

    def __init__(self, config: AdapterConfig):
        """Initialize client with configuration."""
        self.config = config
        self._client = None

    def _get_client(self):
        """Get or create the underlying client instance."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create the underlying client instance. Override in subclasses."""
        raise NotImplementedError

    def close(self):
        """Close client connection."""
        if self._client:
            if hasattr(self._client, "close"):
                self._client.close()
            self._client = None


class AsyncBaseClientWrapper(BaseClientWrapper):
    """Base class for async client wrappers."""

    async def _get_client(self):
        """Get or create the underlying async client instance."""
        if self._client is None:
            self._client = await self._create_client()
        return self._client

    async def _create_client(self):
        """Create the underlying async client instance. Override in subclasses."""
        raise NotImplementedError

    async def close(self):
        """Close async client connection."""
        if self._client:
            if hasattr(self._client, "aclose"):
                await self._client.aclose()
            elif hasattr(self._client, "close"):
                if hasattr(self._client.close, "__aiter__"):
                    await self._client.close()
                else:
                    self._client.close()
            self._client = None
