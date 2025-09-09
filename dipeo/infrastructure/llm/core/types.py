"""Common types for LLM infrastructure."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel

from dipeo.config.llm import DEFAULT_TEMPERATURE
from dipeo.diagram_generated.domain_models import LLMUsage
from dipeo.diagram_generated.enums import ExecutionPhase


class ProviderType(str, Enum):
    """Supported LLM provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"


class StreamingMode(str, Enum):
    """Streaming modes for LLM responses."""

    NONE = "none"
    SSE = "sse"
    WEBSOCKET = "websocket"


@dataclass
class ProviderCapabilities:
    """Capabilities supported by an LLM provider."""

    supports_async: bool = False
    supports_streaming: bool = False
    supports_tools: bool = False
    supports_structured_output: bool = False
    supports_vision: bool = False
    supports_web_search: bool = False
    supports_image_generation: bool = False
    supports_computer_use: bool = False
    max_context_length: int = 4096
    max_output_tokens: int | None = None
    supported_models: set[str] = field(default_factory=set)
    streaming_modes: set[StreamingMode] = field(default_factory=lambda: {StreamingMode.NONE})


@dataclass
class AdapterConfig:
    """Configuration for LLM adapters."""

    provider_type: ProviderType
    model: str
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int | None = None
    timeout: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    execution_phase: ExecutionPhase = ExecutionPhase.DEFAULT
    streaming_mode: StreamingMode = StreamingMode.NONE
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Unified LLM response structure."""

    content: str
    model: str
    provider: ProviderType
    usage: LLMUsage | None = None
    tool_outputs: list[Any] | None = None
    structured_output: Any | None = None
    raw_response: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Compatibility property for code expecting 'text' attribute."""
        return self.content

    @property
    def token_usage(self) -> LLMUsage | None:
        """Compatibility property for code expecting 'token_usage' attribute."""
        return self.usage


class MemorySelectionOutput(BaseModel):
    """Structured output model for memory selection phase."""

    message_ids: list[str]


class DecisionOutput(BaseModel):
    """Structured output model for decision evaluation phase."""

    decision: bool
    # reasoning: str | None = None


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    retry_on_timeout: bool = True
    retry_on_rate_limit: bool = True
    retry_on_server_error: bool = True


@dataclass
class StreamConfig:
    """Configuration for streaming responses."""

    mode: StreamingMode = StreamingMode.NONE
    chunk_size: int = 1024
    buffer_size: int = 4096
    timeout: int = 30


class ProviderError(Exception):
    """Base exception for provider-specific errors."""

    pass


class RateLimitError(ProviderError):
    """Rate limit exceeded error."""

    pass


class AuthenticationError(ProviderError):
    """Authentication failed error."""

    pass


class ModelNotFoundError(ProviderError):
    """Model not found error."""

    pass


class TimeoutError(ProviderError):
    """Request timeout error."""

    pass
