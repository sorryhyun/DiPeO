"""Unified adapter interface for LLM providers."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
from typing import Any

from dipeo.diagram_generated import Message, ToolConfig

from .client import AsyncLLMClient, LLMClient
from .types import (
    AdapterConfig,
    ExecutionPhase,
    LLMResponse,
    ProviderCapabilities,
)


class BaseAdapter(ABC):
    """Base adapter interface for all LLM providers."""

    def __init__(self, config: AdapterConfig):
        """Initialize adapter with configuration."""
        self.config = config
        self.provider_type = config.provider_type
        self.model = config.model
        self._capabilities = self._get_capabilities()

    @abstractmethod
    def _get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities. Override in subclasses."""
        pass

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return self._capabilities

    def supports_feature(self, feature: str) -> bool:
        """Check if provider supports a specific feature."""
        return getattr(self._capabilities, f"supports_{feature}", False)

    @abstractmethod
    def validate_model(self, model: str) -> bool:
        """Validate if model is supported by provider."""
        pass

    def prepare_messages(self, messages: list[Message | dict[str, Any]]) -> list[dict[str, Any]]:
        """Prepare messages for provider API format."""
        prepared = []
        for msg in messages:
            if isinstance(msg, dict):
                # Already a dictionary, just use it
                prepared.append(msg)
            else:
                # Assume it's a Message object
                prepared.append({"role": msg.role, "content": msg.content})
        return prepared

    def process_response(self, raw_response: Any) -> LLMResponse:
        """Process raw provider response into unified format."""
        return LLMResponse(
            content="", model=self.model, provider=self.provider_type, raw_response=raw_response
        )


class SyncAdapter(BaseAdapter):
    """Synchronous adapter interface."""

    def __init__(self, config: AdapterConfig, client: LLMClient | None = None):
        """Initialize sync adapter."""
        super().__init__(config)
        self.client = client or self._create_client()

    @abstractmethod
    def _create_client(self) -> LLMClient:
        """Create the LLM client. Override in subclasses."""
        pass

    def chat(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: Any | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute synchronous chat completion."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        execution_phase = execution_phase or self.config.execution_phase

        prepared_messages = self.prepare_messages(messages)
        api_tools = self._prepare_tools(tools) if tools else None

        raw_response = self.client.chat_completion(
            messages=prepared_messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=api_tools,
            response_format=response_format,
            **kwargs,
        )

        return self.process_response(raw_response)

    def stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Stream synchronous chat completion."""
        if not self.capabilities.supports_streaming:
            raise NotImplementedError(f"{self.provider_type} does not support streaming")

        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        prepared_messages = self.prepare_messages(messages)
        api_tools = self._prepare_tools(tools) if tools else None

        return self.client.stream_chat_completion(
            messages=prepared_messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=api_tools,
            **kwargs,
        )

    def _prepare_tools(self, tools: list[ToolConfig]) -> list[dict[str, Any]]:
        """Prepare tools for provider API format. Override in subclasses."""
        return []


class AsyncAdapter(BaseAdapter):
    """Asynchronous adapter interface."""

    def __init__(self, config: AdapterConfig, client: AsyncLLMClient | None = None):
        """Initialize async adapter."""
        super().__init__(config)
        self.client = client or self._create_client()

    @abstractmethod
    async def _create_client(self) -> AsyncLLMClient:
        """Create the async LLM client. Override in subclasses."""
        pass

    async def chat(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: Any | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute asynchronous chat completion."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        execution_phase = execution_phase or self.config.execution_phase

        prepared_messages = self.prepare_messages(messages)
        api_tools = self._prepare_tools(tools) if tools else None

        raw_response = await self.client.chat_completion(
            messages=prepared_messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=api_tools,
            response_format=response_format,
            **kwargs,
        )

        return self.process_response(raw_response)

    async def stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream asynchronous chat completion."""
        if not self.capabilities.supports_streaming:
            raise NotImplementedError(f"{self.provider_type} does not support streaming")

        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        prepared_messages = self.prepare_messages(messages)
        api_tools = self._prepare_tools(tools) if tools else None

        async for chunk in self.client.stream_chat_completion(
            messages=prepared_messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=api_tools,
            **kwargs,
        ):
            yield chunk

    def _prepare_tools(self, tools: list[ToolConfig]) -> list[dict[str, Any]]:
        """Prepare tools for provider API format. Override in subclasses."""
        return []


class UnifiedAdapter(AsyncAdapter, SyncAdapter):
    """Unified adapter supporting both sync and async operations."""

    def __init__(
        self,
        config: AdapterConfig,
        sync_client: LLMClient | None = None,
        async_client: AsyncLLMClient | None = None,
    ):
        """Initialize unified adapter."""
        BaseAdapter.__init__(self, config)
        self.sync_client = sync_client or self._create_sync_client()
        # Async client will be created lazily when needed
        self._async_client = async_client
        self._async_client_created = False

    @abstractmethod
    def _create_sync_client(self) -> LLMClient:
        """Create the synchronous LLM client. Override in subclasses."""
        pass

    @abstractmethod
    async def _create_async_client(self) -> AsyncLLMClient:
        """Create the asynchronous LLM client. Override in subclasses."""
        pass

    def _create_client(self) -> LLMClient:
        """Create the LLM client (delegates to _create_sync_client)."""
        return self._create_sync_client()

    @property
    def async_client(self) -> AsyncLLMClient:
        """Get or create the async client lazily."""
        if not self._async_client_created:
            import asyncio

            loop = asyncio.new_event_loop()
            self._async_client = loop.run_until_complete(self._create_async_client())
            loop.close()
            self._async_client_created = True
        return self._async_client

    def chat(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: Any | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute synchronous chat completion."""
        return SyncAdapter.chat(
            self,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
            execution_phase=execution_phase,
            **kwargs,
        )

    async def async_chat(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        response_format: Any | None = None,
        execution_phase: ExecutionPhase | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Execute asynchronous chat completion."""
        return await AsyncAdapter.chat(
            self,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
            execution_phase=execution_phase,
            **kwargs,
        )

    def stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Stream synchronous chat completion."""
        return SyncAdapter.stream(
            self,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        )

    async def async_stream(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolConfig] | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream asynchronous chat completion."""
        async for chunk in AsyncAdapter.stream(
            self,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        ):
            yield chunk
