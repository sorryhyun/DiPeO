"""Common types for LLM infrastructure."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel


class ExecutionPhase(str, Enum):
    """Execution phases for DiPeO workflows."""
    MEMORY_SELECTION = "memory_selection"
    DIRECT_EXECUTION = "direct_execution"
    DEFAULT = "default"


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
    max_output_tokens: Optional[int] = None
    supported_models: Set[str] = field(default_factory=set)
    streaming_modes: Set[StreamingMode] = field(default_factory=lambda: {StreamingMode.NONE})


@dataclass
class AdapterConfig:
    """Configuration for LLM adapters."""
    provider_type: ProviderType
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    execution_phase: ExecutionPhase = ExecutionPhase.DEFAULT
    streaming_mode: StreamingMode = StreamingMode.NONE
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenUsage:
    """Token usage statistics."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class LLMResponse:
    """Unified LLM response structure."""
    content: str
    model: str
    provider: ProviderType
    usage: Optional[TokenUsage] = None
    tool_outputs: Optional[List[Any]] = None
    structured_output: Optional[Any] = None
    raw_response: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemorySelectionOutput(BaseModel):
    """Structured output model for memory selection phase."""
    message_ids: List[str]


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