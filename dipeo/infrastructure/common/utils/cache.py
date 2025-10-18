"""Single-flight cache: deduplicates concurrent async operations (only first executes, others wait)."""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)

T = TypeVar("T")


class SingleFlightCache:
    """Deduplicates concurrent requests: first caller executes, others wait for result."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._futures: dict[str, asyncio.Future] = {}
        self._permanent_cache: dict[str, Any] = {}

    async def get_or_create(
        self, key: str, factory: Callable[[], Coroutine[Any, Any, T]], cache_result: bool = True
    ) -> T:
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
        if key:
            self._permanent_cache.pop(key, None)
        else:
            self._permanent_cache.clear()
