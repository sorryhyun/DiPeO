"""Retry logic capability for LLM providers."""

import asyncio
import logging
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from ..drivers.types import (
    AuthenticationError,
    ProviderType,
    RateLimitError,
    RetryConfig,
    TimeoutError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryHandler:
    """Handles retry logic for different providers."""

    def __init__(self, provider: ProviderType, config: RetryConfig):
        """Initialize retry handler for specific provider."""
        self.provider = provider
        self.config = config

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if request should be retried based on error type."""
        if attempt >= self.config.max_attempts:
            return False

        # Never retry authentication errors
        if isinstance(error, AuthenticationError):
            return False

        # Check specific error types
        if isinstance(error, RateLimitError):
            return self.config.retry_on_rate_limit

        if isinstance(error, TimeoutError):
            return self.config.retry_on_timeout

        # Provider-specific error handling
        if self.provider == ProviderType.OPENAI:
            return self._should_retry_openai(error)
        elif self.provider == ProviderType.ANTHROPIC:
            return self._should_retry_anthropic(error)
        elif self.provider == ProviderType.GOOGLE:
            return self._should_retry_google(error)
        elif self.provider == ProviderType.OLLAMA:
            return self._should_retry_ollama(error)

        # Default to retrying on server errors
        return self.config.retry_on_server_error

    def _should_retry_openai(self, error: Exception) -> bool:
        """Check if OpenAI error should be retried."""
        error_str = str(error).lower()

        # OpenAI-specific rate limit patterns
        if "rate limit" in error_str or "quota" in error_str:
            return self.config.retry_on_rate_limit

        # Server errors
        if any(code in error_str for code in ["500", "502", "503", "504"]):
            return self.config.retry_on_server_error

        # Connection errors
        if "connection" in error_str or "timeout" in error_str:
            return self.config.retry_on_timeout

        return False

    def _should_retry_anthropic(self, error: Exception) -> bool:
        """Check if Anthropic error should be retried."""
        error_str = str(error).lower()

        # Anthropic-specific rate limit patterns
        if "rate" in error_str or "overloaded" in error_str:
            return self.config.retry_on_rate_limit

        # Server errors
        if "internal" in error_str or "server" in error_str:
            return self.config.retry_on_server_error

        # Connection errors
        if "connection" in error_str or "timeout" in error_str:
            return self.config.retry_on_timeout

        return False

    def _should_retry_google(self, error: Exception) -> bool:
        """Check if Google error should be retried."""
        error_str = str(error).lower()

        # Google-specific quota patterns
        if "quota" in error_str or "resource_exhausted" in error_str:
            return self.config.retry_on_rate_limit

        # Server errors
        if "unavailable" in error_str or "internal" in error_str:
            return self.config.retry_on_server_error

        # Connection errors
        if "deadline" in error_str or "timeout" in error_str:
            return self.config.retry_on_timeout

        return False

    def _should_retry_ollama(self, error: Exception) -> bool:
        """Check if Ollama error should be retried."""
        error_str = str(error).lower()

        # Connection errors (common with local models)
        if "connection" in error_str or "refused" in error_str:
            return self.config.retry_on_timeout

        # Model loading errors
        return bool("loading" in error_str or "initializing" in error_str)

    def calculate_delay(self, attempt: int, error: Exception | None = None) -> float:
        """Calculate delay before next retry attempt."""
        # Check if error has retry-after header (for rate limits)
        if error and hasattr(error, "retry_after"):
            return float(error.retry_after)

        # Exponential backoff with jitter
        delay = min(
            self.config.initial_delay * (self.config.backoff_factor**attempt), self.config.max_delay
        )

        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, delay * 0.1)

        return delay + jitter

    def with_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for adding retry logic to synchronous functions."""

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(self.config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    if not self.should_retry(e, attempt + 1):
                        logger.error(f"[{self.provider}] Request failed, not retrying: {e}")
                        raise

                    delay = self.calculate_delay(attempt, e)
                    logger.warning(
                        f"[{self.provider}] Request failed (attempt {attempt + 1}/{self.config.max_attempts}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    time.sleep(delay)

            # All retries exhausted
            logger.error(
                f"[{self.provider}] All retry attempts exhausted after {self.config.max_attempts} attempts"
            )
            raise last_error

        return wrapper

    def with_async_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for adding retry logic to asynchronous functions."""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(self.config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    if not self.should_retry(e, attempt + 1):
                        logger.error(f"[{self.provider}] Request failed, not retrying: {e}")
                        raise

                    delay = self.calculate_delay(attempt, e)
                    logger.warning(
                        f"[{self.provider}] Request failed (attempt {attempt + 1}/{self.config.max_attempts}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    await asyncio.sleep(delay)

            # All retries exhausted
            logger.error(
                f"[{self.provider}] All retry attempts exhausted after {self.config.max_attempts} attempts"
            )
            raise last_error

        return wrapper


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        """Initialize circuit breaker."""
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open, not attempting call")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception:
            self._on_failure()
            raise

    async def async_call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute async function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open, not attempting call")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        return (
            self.last_failure_time and time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
