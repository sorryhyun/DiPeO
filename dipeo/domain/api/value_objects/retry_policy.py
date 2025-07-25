"""Retry policy value object."""
from dataclasses import dataclass
from enum import Enum


class RetryStrategy(Enum):
    """Supported retry strategies."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"
    CONSTANT = "constant"


@dataclass(frozen=True)
class RetryPolicy:
    """Represents a retry policy with various strategies."""
    
    max_attempts: int
    initial_delay_ms: int
    max_delay_ms: int
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_factor: float = 2.0
    jitter: bool = True
    
    def __post_init__(self) -> None:
        """Validate the retry policy."""
        if self.max_attempts < 0:
            raise ValueError("max_attempts must be non-negative")
        if self.initial_delay_ms < 0:
            raise ValueError("initial_delay_ms must be non-negative")
        if self.max_delay_ms < self.initial_delay_ms:
            raise ValueError("max_delay_ms must be >= initial_delay_ms")
        if self.backoff_factor <= 0:
            raise ValueError("backoff_factor must be positive")
    
    def calculate_delay(self, attempt: int) -> int:
        """Calculate delay for a given attempt number (0-based)."""
        if attempt < 0:
            raise ValueError("Attempt number must be non-negative")
        
        if attempt == 0:
            return 0  # No delay for first attempt
        
        # Calculate base delay based on strategy
        if self.strategy == RetryStrategy.CONSTANT:
            base_delay = self.initial_delay_ms
        elif self.strategy == RetryStrategy.LINEAR:
            base_delay = self.initial_delay_ms * attempt
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            base_delay = self.initial_delay_ms * (self.backoff_factor ** (attempt - 1))
        elif self.strategy == RetryStrategy.FIBONACCI:
            base_delay = self.initial_delay_ms * self._fibonacci(attempt)
        else:
            base_delay = self.initial_delay_ms
        
        # Apply max delay cap
        delay = min(int(base_delay), self.max_delay_ms)
        
        # Apply jitter if enabled (±20% random variation)
        if self.jitter and delay > 0:
            import random
            jitter_range = int(delay * 0.2)
            delay = delay + random.randint(-jitter_range, jitter_range)
            delay = max(0, delay)  # Ensure non-negative
        
        return delay
    
    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    def should_retry(self, attempt: int, is_retryable_error: bool = True) -> bool:
        """Determine if a retry should be attempted."""
        return is_retryable_error and attempt < self.max_attempts
    
    @property
    def total_possible_delay_ms(self) -> int:
        """Calculate maximum total delay across all retries."""
        total = 0
        for attempt in range(1, self.max_attempts + 1):
            # Calculate without jitter for predictable result
            if self.strategy == RetryStrategy.CONSTANT:
                delay = self.initial_delay_ms
            elif self.strategy == RetryStrategy.LINEAR:
                delay = self.initial_delay_ms * attempt
            elif self.strategy == RetryStrategy.EXPONENTIAL:
                delay = self.initial_delay_ms * (self.backoff_factor ** (attempt - 1))
            elif self.strategy == RetryStrategy.FIBONACCI:
                delay = self.initial_delay_ms * self._fibonacci(attempt)
            else:
                delay = self.initial_delay_ms
            
            total += min(int(delay), self.max_delay_ms)
        
        return total
    
    @classmethod
    def no_retry(cls) -> 'RetryPolicy':
        """Create a policy that doesn't retry."""
        return cls(max_attempts=0, initial_delay_ms=0, max_delay_ms=0)
    
    @classmethod
    def default(cls) -> 'RetryPolicy':
        """Create a sensible default retry policy."""
        return cls(
            max_attempts=3,
            initial_delay_ms=1000,
            max_delay_ms=10000,
            strategy=RetryStrategy.EXPONENTIAL,
            backoff_factor=2.0,
            jitter=True
        )
    
    def __str__(self) -> str:
        """String representation."""
        return (
            f"RetryPolicy(attempts={self.max_attempts}, "
            f"strategy={self.strategy.value}, "
            f"delays={self.initial_delay_ms}-{self.max_delay_ms}ms)"
        )