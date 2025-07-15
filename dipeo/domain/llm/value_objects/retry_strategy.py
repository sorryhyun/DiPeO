"""Retry strategy value object."""

from dataclasses import dataclass
from enum import Enum


class RetryType(Enum):
    """Types of retry strategies."""
    NONE = "none"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE = "immediate"


@dataclass(frozen=True)
class RetryStrategy:
    """Value object representing retry strategy for LLM operations."""
    
    retry_type: RetryType
    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_factor: float = 2.0
    
    def __post_init__(self):
        """Validate retry strategy parameters."""
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.initial_delay_seconds < 0:
            raise ValueError("Initial delay cannot be negative")
        if self.max_delay_seconds < self.initial_delay_seconds:
            raise ValueError("Max delay must be >= initial delay")
        if self.backoff_factor <= 0:
            raise ValueError("Backoff factor must be positive")
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given retry attempt."""
        if self.retry_type == RetryType.NONE:
            return 0.0
        if self.retry_type == RetryType.IMMEDIATE:
            return 0.0
        if self.retry_type == RetryType.LINEAR_BACKOFF:
            delay = self.initial_delay_seconds * attempt
        else:  # EXPONENTIAL_BACKOFF
            delay = self.initial_delay_seconds * (self.backoff_factor ** (attempt - 1))
        
        return min(delay, self.max_delay_seconds)
    
    def should_retry(self, attempt: int) -> bool:
        """Check if we should retry based on attempt number."""
        if self.retry_type == RetryType.NONE:
            return False
        return attempt <= self.max_retries
    
    @classmethod
    def no_retry(cls) -> "RetryStrategy":
        """Create a no-retry strategy."""
        return cls(retry_type=RetryType.NONE, max_retries=0)
    
    @classmethod
    def default(cls) -> "RetryStrategy":
        """Create a default retry strategy."""
        return cls(
            retry_type=RetryType.EXPONENTIAL_BACKOFF,
            max_retries=3,
            initial_delay_seconds=1.0,
            max_delay_seconds=60.0,
            backoff_factor=2.0
        )