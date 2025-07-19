import asyncio
import logging
from functools import wraps
from typing import Callable, Optional, TypeVar, Union, Any
from dipeo.core.exceptions import LLMRateLimitError, LLMAPIError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStrategy:
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        delay = min(self.initial_delay * (self.exponential_base ** attempt), self.max_delay)
        if self.jitter:
            import random
            delay *= (0.5 + random.random())
        return delay


class RetryManager:
    
    DEFAULT_STRATEGY = RetryStrategy()
    RATE_LIMIT_STRATEGY = RetryStrategy(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=120.0,
        exponential_base=2.5
    )

    @classmethod
    def get_strategy_for_error(cls, error: Exception) -> Optional[RetryStrategy]:
        if isinstance(error, LLMRateLimitError):
            return cls.RATE_LIMIT_STRATEGY
        elif isinstance(error, LLMAPIError):
            return cls.DEFAULT_STRATEGY
        return None

    @classmethod
    def with_retry(
        cls,
        strategy: Optional[RetryStrategy] = None,
        retryable_errors: tuple = (LLMAPIError, LLMRateLimitError)
    ):
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                return await cls._execute_with_retry_async(
                    func, args, kwargs, strategy or cls.DEFAULT_STRATEGY, retryable_errors
                )

            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                return cls._execute_with_retry_sync(
                    func, args, kwargs, strategy or cls.DEFAULT_STRATEGY, retryable_errors
                )

            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    @classmethod
    async def _execute_with_retry_async(
        cls,
        func: Callable,
        args: tuple,
        kwargs: dict,
        strategy: RetryStrategy,
        retryable_errors: tuple
    ) -> Any:
        last_error = None
        
        for attempt in range(strategy.max_attempts):
            try:
                return await func(*args, **kwargs)
            except retryable_errors as e:
                last_error = e
                
                # Check if we should use a different strategy for this error
                error_strategy = cls.get_strategy_for_error(e) or strategy
                
                if attempt < error_strategy.max_attempts - 1:
                    delay = error_strategy.calculate_delay(attempt)
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{error_strategy.max_attempts} "
                        f"after {type(e).__name__}: {str(e)}. "
                        f"Waiting {delay:.1f}s before retry."
                    )
                    await asyncio.sleep(delay)
                else:
                    break
            except Exception as e:
                # Non-retryable errors
                raise

        if last_error:
            logger.error(f"All retry attempts exhausted. Last error: {last_error}")
            raise last_error

    @classmethod
    def _execute_with_retry_sync(
        cls,
        func: Callable,
        args: tuple,
        kwargs: dict,
        strategy: RetryStrategy,
        retryable_errors: tuple
    ) -> Any:
        last_error = None
        
        for attempt in range(strategy.max_attempts):
            try:
                return func(*args, **kwargs)
            except retryable_errors as e:
                last_error = e
                
                # Check if we should use a different strategy for this error
                error_strategy = cls.get_strategy_for_error(e) or strategy
                
                if attempt < error_strategy.max_attempts - 1:
                    delay = error_strategy.calculate_delay(attempt)
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{error_strategy.max_attempts} "
                        f"after {type(e).__name__}: {str(e)}. "
                        f"Waiting {delay:.1f}s before retry."
                    )
                    import time
                    time.sleep(delay)
                else:
                    break
            except Exception as e:
                # Non-retryable errors
                raise

        if last_error:
            logger.error(f"All retry attempts exhausted. Last error: {last_error}")
            raise last_error