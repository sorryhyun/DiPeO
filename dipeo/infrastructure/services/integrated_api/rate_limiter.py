"""Rate limiting implementations for API providers."""

import asyncio
import logging
import time
from typing import Optional
from collections import defaultdict, deque

from dipeo.infrastructure.services.integrated_api.manifest_schema import (
    RateLimitConfig,
    RateLimitAlgorithm
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter implementation supporting multiple algorithms."""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize rate limiter.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.algorithm = config.algorithm
        
        # Initialize algorithm-specific state
        if self.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            self._token_bucket = TokenBucket(
                capacity=config.capacity,
                refill_rate=config.refill_per_sec
            )
        elif self.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            self._sliding_window = SlidingWindow(
                window_size=config.window_size_sec,
                max_requests=config.capacity
            )
        elif self.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            self._fixed_window = FixedWindow(
                window_size=config.window_size_sec,
                max_requests=config.capacity
            )
        elif self.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            self._leaky_bucket = LeakyBucket(
                capacity=config.capacity,
                leak_rate=config.refill_per_sec
            )
        else:
            # No rate limiting
            self._no_limit = True
    
    async def acquire(self, operation: Optional[str] = None) -> None:
        """Acquire permission to make a request.
        
        This method will block until the request can proceed
        according to the rate limit.
        
        Args:
            operation: Optional operation name for per-operation limits
        """
        if hasattr(self, '_no_limit'):
            return
        
        if self.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            await self._token_bucket.acquire()
        elif self.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            await self._sliding_window.acquire()
        elif self.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            await self._fixed_window.acquire()
        elif self.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            await self._leaky_bucket.acquire()
    
    def can_proceed(self, operation: Optional[str] = None) -> bool:
        """Check if a request can proceed without blocking.
        
        Args:
            operation: Optional operation name
            
        Returns:
            True if request can proceed, False otherwise
        """
        if hasattr(self, '_no_limit'):
            return True
        
        if self.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return self._token_bucket.can_proceed()
        elif self.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return self._sliding_window.can_proceed()
        elif self.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return self._fixed_window.can_proceed()
        elif self.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            return self._leaky_bucket.can_proceed()
        
        return True
    
    def reset(self) -> None:
        """Reset rate limiter state."""
        if hasattr(self, '_token_bucket'):
            self._token_bucket.reset()
        elif hasattr(self, '_sliding_window'):
            self._sliding_window.reset()
        elif hasattr(self, '_fixed_window'):
            self._fixed_window.reset()
        elif hasattr(self, '_leaky_bucket'):
            self._leaky_bucket.reset()


class TokenBucket:
    """Token bucket rate limiting algorithm.
    
    Tokens are added at a constant rate and consumed by requests.
    Requests can burst up to the bucket capacity.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token, blocking if necessary."""
        async with self._lock:
            while True:
                self._refill()
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                
                # Calculate wait time
                wait_time = (1 - self.tokens) / self.refill_rate
                await asyncio.sleep(wait_time)
    
    def can_proceed(self) -> bool:
        """Check if a token is available."""
        self._refill()
        return self.tokens >= 1
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def reset(self) -> None:
        """Reset to full capacity."""
        self.tokens = self.capacity
        self.last_refill = time.monotonic()


class SlidingWindow:
    """Sliding window rate limiting algorithm.
    
    Tracks requests in a sliding time window.
    """
    
    def __init__(self, window_size: int, max_requests: int):
        """Initialize sliding window.
        
        Args:
            window_size: Window size in seconds
            max_requests: Maximum requests in window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            while True:
                self._cleanup_old_requests()
                
                if len(self.requests) < self.max_requests:
                    self.requests.append(time.monotonic())
                    return
                
                # Calculate wait time until oldest request expires
                oldest = self.requests[0]
                wait_time = self.window_size - (time.monotonic() - oldest)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
    
    def can_proceed(self) -> bool:
        """Check if a request can proceed."""
        self._cleanup_old_requests()
        return len(self.requests) < self.max_requests
    
    def _cleanup_old_requests(self) -> None:
        """Remove requests outside the window."""
        now = time.monotonic()
        cutoff = now - self.window_size
        
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
    
    def reset(self) -> None:
        """Clear all requests."""
        self.requests.clear()


class FixedWindow:
    """Fixed window rate limiting algorithm.
    
    Resets request count at fixed intervals.
    """
    
    def __init__(self, window_size: int, max_requests: int):
        """Initialize fixed window.
        
        Args:
            window_size: Window size in seconds
            max_requests: Maximum requests per window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.window_start = time.monotonic()
        self.request_count = 0
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            while True:
                self._check_window()
                
                if self.request_count < self.max_requests:
                    self.request_count += 1
                    return
                
                # Calculate wait time until window resets
                elapsed = time.monotonic() - self.window_start
                wait_time = self.window_size - elapsed
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
    
    def can_proceed(self) -> bool:
        """Check if a request can proceed."""
        self._check_window()
        return self.request_count < self.max_requests
    
    def _check_window(self) -> None:
        """Check if window should reset."""
        now = time.monotonic()
        elapsed = now - self.window_start
        
        if elapsed >= self.window_size:
            self.window_start = now
            self.request_count = 0
    
    def reset(self) -> None:
        """Reset the window."""
        self.window_start = time.monotonic()
        self.request_count = 0


class LeakyBucket:
    """Leaky bucket rate limiting algorithm.
    
    Requests are added to a bucket that leaks at a constant rate.
    """
    
    def __init__(self, capacity: int, leak_rate: float):
        """Initialize leaky bucket.
        
        Args:
            capacity: Maximum bucket size
            leak_rate: Requests leaked per second
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.level = 0
        self.last_leak = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            while True:
                self._leak()
                
                if self.level < self.capacity:
                    self.level += 1
                    return
                
                # Calculate wait time for leak
                wait_time = 1.0 / self.leak_rate
                await asyncio.sleep(wait_time)
    
    def can_proceed(self) -> bool:
        """Check if a request can proceed."""
        self._leak()
        return self.level < self.capacity
    
    def _leak(self) -> None:
        """Leak requests based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_leak
        leak_amount = elapsed * self.leak_rate
        
        self.level = max(0, self.level - leak_amount)
        self.last_leak = now
    
    def reset(self) -> None:
        """Reset bucket level."""
        self.level = 0
        self.last_leak = time.monotonic()


class PerOperationRateLimiter:
    """Rate limiter that supports per-operation limits."""
    
    def __init__(self, default_config: RateLimitConfig):
        """Initialize per-operation rate limiter.
        
        Args:
            default_config: Default rate limit configuration
        """
        self.default_config = default_config
        self.default_limiter = RateLimiter(default_config)
        self.operation_limiters: dict[str, RateLimiter] = {}
    
    def add_operation_limit(self, operation: str, config: RateLimitConfig) -> None:
        """Add operation-specific rate limit.
        
        Args:
            operation: Operation name
            config: Rate limit configuration
        """
        self.operation_limiters[operation] = RateLimiter(config)
    
    async def acquire(self, operation: Optional[str] = None) -> None:
        """Acquire permission for an operation.
        
        Args:
            operation: Operation name
        """
        if operation and operation in self.operation_limiters:
            await self.operation_limiters[operation].acquire()
        else:
            await self.default_limiter.acquire()
    
    def can_proceed(self, operation: Optional[str] = None) -> bool:
        """Check if an operation can proceed.
        
        Args:
            operation: Operation name
            
        Returns:
            True if can proceed
        """
        if operation and operation in self.operation_limiters:
            return self.operation_limiters[operation].can_proceed()
        else:
            return self.default_limiter.can_proceed()
    
    def reset(self, operation: Optional[str] = None) -> None:
        """Reset rate limiter.
        
        Args:
            operation: Operation to reset, or None for all
        """
        if operation:
            if operation in self.operation_limiters:
                self.operation_limiters[operation].reset()
        else:
            self.default_limiter.reset()
            for limiter in self.operation_limiters.values():
                limiter.reset()