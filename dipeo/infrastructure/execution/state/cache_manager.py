"""Cache management for cache-first state store."""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import ExecutionState, Status

from .models import CacheEntry, CacheMetrics

logger = get_module_logger(__name__)


class CacheManager:
    """Manages cache operations, eviction, and warm cache."""

    def __init__(
        self,
        cache_size: int = 1000,
        warm_cache_size: int = 20,
    ):
        # Cache configuration
        self._cache: dict[str, CacheEntry] = {}
        self._cache_size = cache_size
        self._cache_lock = asyncio.Lock()

        # Frequently accessed executions (for cache warming)
        self._access_frequency: defaultdict[str, int] = defaultdict(int)
        self._warm_cache_size = warm_cache_size
        self._warm_cache_ids: set[str] = set()

        # Metrics
        self._metrics = CacheMetrics()

        # State
        self._running = False

    @property
    def cache(self) -> dict[str, CacheEntry]:
        """Get cache dictionary."""
        return self._cache

    @property
    def cache_lock(self) -> asyncio.Lock:
        """Get cache lock."""
        return self._cache_lock

    @property
    def metrics(self) -> CacheMetrics:
        """Get cache metrics."""
        return self._metrics

    async def has_execution(self, execution_id: str) -> bool:
        """Check if execution exists in cache."""
        async with self._cache_lock:
            return execution_id in self._cache

    async def get_entry(self, execution_id: str) -> CacheEntry | None:
        """Get cache entry if exists."""
        async with self._cache_lock:
            if execution_id in self._cache:
                entry = self._cache[execution_id]
                entry.touch()
                self._access_frequency[execution_id] += 1

                if execution_id in self._warm_cache_ids:
                    self._metrics.warm_cache_hits += 1
                else:
                    self._metrics.cache_hits += 1

                return entry

        self._metrics.cache_misses += 1
        return None

    async def put_entry(self, execution_id: str, entry: CacheEntry) -> None:
        """Put entry in cache."""
        async with self._cache_lock:
            self._cache[execution_id] = entry

    async def update_entry(
        self,
        execution_id: str,
        update_func: Callable,
    ) -> CacheEntry:
        """Update cache entry with a function."""
        async with self._cache_lock:
            if execution_id in self._cache:
                entry = self._cache[execution_id]
            else:
                raise ValueError(f"Execution {execution_id} not in cache")

            update_func(entry)
            entry.mark_dirty()
            return entry

    async def remove_entry(self, execution_id: str) -> CacheEntry | None:
        """Remove entry from cache."""
        async with self._cache_lock:
            return self._cache.pop(execution_id, None)

    async def mark_warm(self, execution_id: str) -> None:
        """Mark an execution as part of warm cache."""
        async with self._cache_lock:
            self._warm_cache_ids.add(execution_id)

    async def warm_cache_with_states(self, states: list[tuple[ExecutionState, int]]) -> None:
        """Warm cache with pre-loaded states."""
        for state, access_count in states:
            exec_id = state.id

            # Create cache entry
            entry = CacheEntry(
                state=state,
                is_persisted=True,
                access_count=access_count,
            )

            # Populate node data
            for node_id, node_state in state.node_states.items():
                entry.node_statuses[node_id] = node_state.status
                if node_state.error:
                    entry.node_errors[node_id] = node_state.error

            entry.node_outputs = state.node_outputs.copy()
            entry.variables = state.variables.copy()
            entry.llm_usage = state.llm_usage

            async with self._cache_lock:
                self._cache[exec_id] = entry
                self._warm_cache_ids.add(exec_id)

    async def evict_if_needed(self, persist_callback: Callable | None = None) -> None:
        """Evict cache entries if cache is full."""
        async with self._cache_lock:
            if len(self._cache) <= self._cache_size:
                return

            # Sort by access time and frequency
            entries = [
                (exec_id, entry)
                for exec_id, entry in self._cache.items()
                if exec_id not in self._warm_cache_ids  # Don't evict warm cache
            ]

            entries.sort(key=lambda x: (x[1].access_count, x[1].last_access_time))

            # Evict least recently/frequently used
            evict_count = len(self._cache) - int(self._cache_size * 0.9)  # Keep 90% full

            for exec_id, entry in entries[:evict_count]:
                if entry.is_dirty and persist_callback:
                    await persist_callback(exec_id, entry)
                del self._cache[exec_id]
                self._metrics.cache_evictions += 1

    async def update_warm_cache(self) -> None:
        """Update the warm cache based on access patterns."""
        # Find most frequently accessed executions
        top_accessed = sorted(self._access_frequency.items(), key=lambda x: x[1], reverse=True)[
            : self._warm_cache_size
        ]

        new_warm_ids = {exec_id for exec_id, _ in top_accessed}

        # Update warm cache IDs
        async with self._cache_lock:
            self._warm_cache_ids = new_warm_ids

        # Reset access frequency counter
        self._access_frequency.clear()

    async def get_dirty_entries(
        self, age_threshold: float | None = None
    ) -> list[tuple[str, CacheEntry]]:
        """Get all dirty entries, optionally filtered by age."""
        import time

        current_time = time.time()

        async with self._cache_lock:
            dirty_entries = []
            for exec_id, entry in self._cache.items():
                if entry.is_dirty:
                    if age_threshold is None:
                        dirty_entries.append((exec_id, entry))
                    else:
                        time_since_write = current_time - entry.last_write_time
                        if time_since_write >= age_threshold:
                            dirty_entries.append((exec_id, entry))
            return dirty_entries

    async def get_all_dirty_entries(self) -> list[tuple[str, CacheEntry]]:
        """Get all dirty cache entries."""
        async with self._cache_lock:
            return [(exec_id, entry) for exec_id, entry in self._cache.items() if entry.is_dirty]

    async def start_background_tasks(self) -> tuple[asyncio.Task, asyncio.Task]:
        """Start background tasks for cache management."""
        self._running = True

        cache_management_task = asyncio.create_task(self._cache_management_loop())
        warmup_task = asyncio.create_task(self._cache_warmup_loop())

        return cache_management_task, warmup_task

    async def stop_background_tasks(self) -> None:
        """Stop background tasks."""
        self._running = False

    async def _cache_management_loop(self) -> None:
        """Background task to manage cache size and eviction."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self.evict_if_needed()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache management loop: {e}", exc_info=True)

    async def _cache_warmup_loop(self) -> None:
        """Background task to update warm cache based on access patterns."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                await self.update_warm_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache warmup loop: {e}", exc_info=True)
