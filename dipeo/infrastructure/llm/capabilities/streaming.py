"""Streaming capability for LLM providers."""

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

from ..core.types import ProviderType, StreamConfig, StreamingMode

logger = logging.getLogger(__name__)


class StreamingHandler:
    """Handles streaming responses for different providers."""

    def __init__(self, provider: ProviderType, config: StreamConfig):
        """Initialize streaming handler for specific provider."""
        self.provider = provider
        self.config = config

    def process_stream_chunk(self, chunk: Any) -> str | None:
        """Process a single stream chunk from provider."""
        if self.provider == ProviderType.OPENAI:
            return self._process_openai_chunk(chunk)
        elif self.provider == ProviderType.ANTHROPIC:
            return self._process_anthropic_chunk(chunk)
        elif self.provider == ProviderType.GOOGLE:
            return self._process_google_chunk(chunk)
        elif self.provider == ProviderType.OLLAMA:
            return self._process_ollama_chunk(chunk)
        else:
            return None

    def _process_openai_chunk(self, chunk: Any) -> str | None:
        """Process OpenAI stream chunk."""
        if hasattr(chunk, "choices") and chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                return delta.content
        return None

    def _process_anthropic_chunk(self, chunk: Any) -> str | None:
        """Process Anthropic/Claude stream chunk."""
        if chunk.type == "content_block_delta":
            if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                return chunk.delta.text
        elif chunk.type == "text" and hasattr(chunk, "text"):
            return chunk.text
        return None

    def _process_google_chunk(self, chunk: Any) -> str | None:
        """Process Google/Gemini stream chunk."""
        if hasattr(chunk, "text"):
            return chunk.text
        elif hasattr(chunk, "candidates") and chunk.candidates:
            for candidate in chunk.candidates:
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    for part in candidate.content.parts:
                        if hasattr(part, "text"):
                            return part.text
        return None

    def _process_ollama_chunk(self, chunk: Any) -> str | None:
        """Process Ollama stream chunk."""
        if isinstance(chunk, dict):
            return chunk.get("response", "")
        elif isinstance(chunk, str):
            try:
                data = json.loads(chunk)
                return data.get("response", "")
            except json.JSONDecodeError:
                return chunk
        return None

    def create_sync_stream_wrapper(self, stream: Iterator[Any]) -> Iterator[str]:
        """Wrap provider stream with chunk processing."""
        for chunk in stream:
            processed = self.process_stream_chunk(chunk)
            if processed:
                yield processed

    async def create_async_stream_wrapper(self, stream: AsyncIterator[Any]) -> AsyncIterator[str]:
        """Wrap async provider stream with chunk processing."""
        async for chunk in stream:
            processed = self.process_stream_chunk(chunk)
            if processed:
                yield processed

    def format_sse_message(self, content: str, event: str = "message") -> str:
        """Format content as Server-Sent Events message."""
        if self.config.mode != StreamingMode.SSE:
            return content

        lines = []
        if event != "message":
            lines.append(f"event: {event}")

        # Handle multi-line content
        for line in content.split("\n"):
            lines.append(f"data: {line}")

        lines.append("")  # Empty line to signal end of message
        return "\n".join(lines)

    def format_websocket_message(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Format content as WebSocket message."""
        if self.config.mode != StreamingMode.WEBSOCKET:
            return content

        message = {"type": "stream", "content": content}

        if metadata:
            message["metadata"] = metadata

        return json.dumps(message)


class StreamBuffer:
    """Buffer for accumulating streamed content."""

    def __init__(self, buffer_size: int = 4096):
        """Initialize stream buffer."""
        self.buffer = []
        self.buffer_size = buffer_size
        self.total_chars = 0

    def add(self, content: str) -> None:
        """Add content to buffer."""
        self.buffer.append(content)
        self.total_chars += len(content)

        # Manage buffer size
        while self.total_chars > self.buffer_size and len(self.buffer) > 1:
            removed = self.buffer.pop(0)
            self.total_chars -= len(removed)

    def get_full_content(self) -> str:
        """Get accumulated content."""
        return "".join(self.buffer)

    def clear(self) -> None:
        """Clear the buffer."""
        self.buffer.clear()
        self.total_chars = 0


class StreamAggregator:
    """Aggregates streamed chunks for final processing."""

    def __init__(self):
        """Initialize stream aggregator."""
        self.content_buffer = StreamBuffer()
        self.metadata = {}
        self.tool_calls = []
        self.usage_data = None

    def process_chunk(self, chunk: Any, provider: ProviderType) -> None:
        """Process and aggregate a stream chunk."""
        # Extract content
        handler = StreamingHandler(provider, StreamConfig())
        content = handler.process_stream_chunk(chunk)
        if content:
            self.content_buffer.add(content)

        # Extract metadata based on provider
        if provider == ProviderType.OPENAI:
            self._aggregate_openai_metadata(chunk)
        elif provider == ProviderType.ANTHROPIC:
            self._aggregate_anthropic_metadata(chunk)

    def _aggregate_openai_metadata(self, chunk: Any) -> None:
        """Aggregate OpenAI-specific metadata."""
        if hasattr(chunk, "usage"):
            self.usage_data = chunk.usage

        if hasattr(chunk, "choices") and chunk.choices:
            choice = chunk.choices[0]
            if hasattr(choice, "finish_reason"):
                self.metadata["finish_reason"] = choice.finish_reason

            # Tool calls
            if hasattr(choice.delta, "tool_calls"):
                self.tool_calls.extend(choice.delta.tool_calls or [])

    def _aggregate_anthropic_metadata(self, chunk: Any) -> None:
        """Aggregate Anthropic-specific metadata."""
        if chunk.type == "message_start" and hasattr(chunk, "message"):
            if hasattr(chunk.message, "usage"):
                self.usage_data = chunk.message.usage

        elif chunk.type == "message_delta" and hasattr(chunk, "usage"):
            self.usage_data = chunk.usage

        elif chunk.type == "content_block_start":
            if hasattr(chunk, "content_block") and chunk.content_block.type == "tool_use":
                self.tool_calls.append(chunk.content_block)

    def get_final_response(self) -> dict[str, Any]:
        """Get the final aggregated response."""
        return {
            "content": self.content_buffer.get_full_content(),
            "usage": self.usage_data,
            "tool_calls": self.tool_calls,
            "metadata": self.metadata,
        }
