"""Single-flight cache for deduplicating concurrent async operations.

This pattern ensures that when multiple coroutines request the same resource
concurrently, only one actually performs the expensive operation (e.g., pulling
a model) while others wait for its result.
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SingleFlightCache:
    """Cache that deduplicates concurrent requests for the same key.
    
    When multiple coroutines request the same key simultaneously:
    - The first becomes the "leader" and executes the factory function
    - Others become "followers" and wait for the leader's result
    - All get the same result (or exception)
    
    This is particularly useful for operations like:
    - Model downloading/pulling
    - Expensive API calls
    - Database lookups
    """
    
    def __init__(self):
        """Initialize the single-flight cache."""
        self._lock = asyncio.Lock()
        self._futures: Dict[str, asyncio.Future] = {}
        self._permanent_cache: Dict[str, Any] = {}
    
    async def get_or_create(
        self,
        key: str,
        factory: Callable[[], Coroutine[Any, Any, T]],
        cache_result: bool = True
    ) -> T:
        """Get a value from cache or create it using the factory.
        
        Args:
            key: Cache key to identify the resource
            factory: Async function that creates the resource
            cache_result: If True, cache the result permanently
            
        Returns:
            The cached or newly created resource
            
        Raises:
            Any exception raised by the factory function
        """
        # Check permanent cache first
        if cache_result and key in self._permanent_cache:
            logger.debug(f"SingleFlightCache: Returning permanently cached result for {key}")
            return self._permanent_cache[key]
        
        # Acquire lock to check/modify futures dict
        async with self._lock:
            fut = self._futures.get(key)
            if fut is None:
                # First coroutine becomes the leader
                fut = self._futures[key] = asyncio.get_event_loop().create_future()
                is_leader = True
                logger.debug(f"SingleFlightCache: Became leader for {key}")
            else:
                # Subsequent coroutines become followers
                is_leader = False
                logger.debug(f"SingleFlightCache: Became follower for {key}")
        
        if is_leader:
            try:
                # Leader executes the factory function
                logger.info(f"SingleFlightCache: Leader executing factory for {key}")
                result = await factory()
                
                # Cache the result if requested
                if cache_result:
                    self._permanent_cache[key] = result
                
                # Set result for all followers
                fut.set_result(result)
                logger.info(f"SingleFlightCache: Leader completed successfully for {key}")
            except Exception as exc:
                # Set exception for all followers
                fut.set_exception(exc)
                logger.error(f"SingleFlightCache: Leader failed for {key}: {exc}")
                raise
            finally:
                # Clean up the future after some time to allow stragglers
                async def cleanup():
                    await asyncio.sleep(0.1)  # Small delay for any stragglers
                    async with self._lock:
                        if key in self._futures and self._futures[key] is fut:
                            del self._futures[key]
                            logger.debug(f"SingleFlightCache: Cleaned up future for {key}")
                
                asyncio.create_task(cleanup())
            
            return result
        else:
            # Followers wait for the leader's result
            logger.debug(f"SingleFlightCache: Follower waiting for {key}")
            try:
                result = await fut
                logger.debug(f"SingleFlightCache: Follower got result for {key}")
                return result
            except Exception as exc:
                logger.debug(f"SingleFlightCache: Follower got exception for {key}: {exc}")
                raise
    
    def clear(self, key: Optional[str] = None):
        """Clear cached results.
        
        Args:
            key: If provided, clear only this key. Otherwise clear all.
        """
        if key:
            self._permanent_cache.pop(key, None)
            logger.debug(f"SingleFlightCache: Cleared cache for {key}")
        else:
            self._permanent_cache.clear()
            logger.debug("SingleFlightCache: Cleared all cache")