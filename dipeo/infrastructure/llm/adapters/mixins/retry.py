"""Retry logic mixin for async LLM operations."""

import asyncio
import logging
from typing import Any, Callable, TypeVar, Optional

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncRetryMixin:
    """Mixin providing async retry capabilities with exponential backoff."""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def _is_retriable_error(self, error: Exception) -> bool:
        """Check if an error is retriable."""
        error_str = str(error).lower()
        retriable_keywords = [
            "timeout", "timed out", "connection", "network",
            "unavailable", "service_unavailable", "internal_error",
            "overloaded"
        ]
        return any(keyword in error_str for keyword in retriable_keywords)
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error."""
        error_str = str(error).lower()
        return "rate_limit" in error_str or "429" in error_str
    
    async def _retry_with_backoff(
        self,
        func: Callable[..., T],
        *args,
        on_empty_response: Optional[Callable[[str], T]] = None,
        error_message_prefix: str = "API call",
        **kwargs
    ) -> T:
        """
        Execute a function with exponential backoff retry logic.
        
        Args:
            func: The async function to retry
            *args: Positional arguments for func
            on_empty_response: Optional function to create empty response on failure
            error_message_prefix: Prefix for error messages
            **kwargs: Keyword arguments for func
        
        Returns:
            The result of the function call
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if self._is_rate_limit_error(e):
                    if attempt < self.max_retries - 1:
                        # Calculate exponential backoff
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(
                            f"Rate limit hit, retrying in {delay} seconds... "
                            f"(attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                
                # Log error
                logger.error(f"{error_message_prefix} error: {error_msg}")
                
                # Retry for connection errors
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Retrying after error: {e} (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue
                
                # For final attempt or non-retriable errors
                if attempt == self.max_retries - 1:
                    logger.error(f"All retry attempts exhausted for {error_message_prefix}")
                    if on_empty_response:
                        return on_empty_response(
                            f"{error_message_prefix} failed after {self.max_retries} attempts"
                        )
                    raise
        
        # If we've exhausted all retries
        if on_empty_response:
            return on_empty_response(f"Failed to get response from {error_message_prefix}")
        
        if last_exception:
            raise last_exception
        
        raise RuntimeError(f"Unexpected retry exit for {error_message_prefix}")