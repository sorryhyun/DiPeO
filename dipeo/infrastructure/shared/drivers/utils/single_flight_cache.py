"""Single-flight cache for deduplicating concurrent async operations.

This pattern ensures that when multiple coroutines request the same resource
concurrently, only one actually performs the expensive operation (e.g., pulling
a model) while others wait for its result.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

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
        self._lock = asyncio.Lock()
        self._futures: dict[str, asyncio.Future] = {}
        self._permanent_cache: dict[str, Any] = {}

    async def get_or_create(
        self, key: str, factory: Callable[[], Coroutine[Any, Any, T]], cache_result: bool = True
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
        if cache_result and key in self._permanent_cache:
            return self._permanent_cache[key]

        async with self._lock:
            fut = self._futures.get(key)
            if fut is None:
                fut = self._futures[key] = asyncio.get_event_loop().create_future()
                is_leader = True
            else:
                is_leader = False

        if is_leader:
            try:
                result = await factory()

                if cache_result:
                    self._permanent_cache[key] = result

                fut.set_result(result)
            except Exception as exc:
                fut.set_exception(exc)
                logger.error(f"SingleFlightCache: Leader failed for {key}: {exc}")
                raise
            finally:

                async def cleanup():
                    await asyncio.sleep(0.1)
                    async with self._lock:
                        if key in self._futures and self._futures[key] is fut:
                            del self._futures[key]

                task = asyncio.create_task(cleanup())
                task.add_done_callback(lambda t: None)

            return result
        else:
            try:
                result = await fut
                return result
            except Exception:
                raise

    def clear(self, key: str | None = None):
        """Clear cached results for specific key or all keys."""
        if key:
            self._permanent_cache.pop(key, None)
        else:
            self._permanent_cache.clear()
