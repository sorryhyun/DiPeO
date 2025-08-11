"""Per-execution state cache to eliminate global lock contention."""

import asyncio
import logging
import time
from typing import Any

from dipeo.diagram_generated import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    Status,
    TokenUsage,
)

logger = logging.getLogger(__name__)


class ExecutionCache:
    """Per-execution cache without global locks."""
    
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.state: ExecutionState | None = None
        self.node_outputs: dict[str, Any] = {}
        self.node_statuses: dict[str, Status] = {}
        self.node_errors: dict[str, str] = {}
        self.variables: dict[str, Any] = {}
        self.token_usage: TokenUsage | None = None
        self._local_lock = asyncio.Lock()  # Per-execution lock
        self._last_access = time.time()
        self._dirty = False  # Track if cache needs persistence
    
    async def get_state(self) -> ExecutionState | None:
        """Get the cached execution state."""
        async with self._local_lock:
            self._last_access = time.time()
            return self.state
    
    async def set_state(self, state: ExecutionState) -> None:
        """Set the execution state."""
        async with self._local_lock:
            self.state = state
            self._last_access = time.time()
            self._dirty = True
    
    async def get_node_output(self, node_id: str) -> Any:
        """Get output for a specific node."""
        async with self._local_lock:
            self._last_access = time.time()
            return self.node_outputs.get(node_id)
    
    async def set_node_output(self, node_id: str, output: Any) -> None:
        """Set output for a specific node."""
        async with self._local_lock:
            self.node_outputs[node_id] = output
            self._last_access = time.time()
            self._dirty = True
    
    async def get_node_status(self, node_id: str) -> Status | None:
        """Get status for a specific node."""
        async with self._local_lock:
            self._last_access = time.time()
            return self.node_statuses.get(node_id)
    
    async def set_node_status(
        self, node_id: str, status: Status, error: str | None = None
    ) -> None:
        """Set status for a specific node."""
        async with self._local_lock:
            self.node_statuses[node_id] = status
            if error:
                self.node_errors[node_id] = error
            elif node_id in self.node_errors:
                del self.node_errors[node_id]
            self._last_access = time.time()
            self._dirty = True
    
    async def update_variables(self, variables: dict[str, Any]) -> None:
        """Update execution variables."""
        async with self._local_lock:
            self.variables.update(variables)
            self._last_access = time.time()
            self._dirty = True
    
    async def update_token_usage(self, tokens: TokenUsage) -> None:
        """Update token usage."""
        async with self._local_lock:
            self.token_usage = tokens
            self._last_access = time.time()
            self._dirty = True
    
    async def add_token_usage(self, tokens: TokenUsage) -> None:
        """Add to token usage."""
        async with self._local_lock:
            if self.token_usage is None:
                self.token_usage = tokens
            else:
                # Add token counts
                self.token_usage = TokenUsage(
                    input=self.token_usage.input + tokens.input,
                    output=self.token_usage.output + tokens.output,
                    cached=(self.token_usage.cached or 0) + (tokens.cached or 0) if tokens.cached else self.token_usage.cached,
                    total=self.token_usage.input + tokens.input + self.token_usage.output + tokens.output,
                )
            self._last_access = time.time()
            self._dirty = True
    
    def is_dirty(self) -> bool:
        """Check if cache has unpersisted changes."""
        return self._dirty
    
    def mark_clean(self) -> None:
        """Mark cache as clean (persisted)."""
        self._dirty = False
    
    def get_last_access_time(self) -> float:
        """Get the last access timestamp."""
        return self._last_access


class ExecutionStateCache:
    """Manages per-execution caches to eliminate global lock contention."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self._caches: dict[str, ExecutionCache] = {}
        self._cache_lock = asyncio.Lock()  # Only for cache creation/deletion
        self._ttl_seconds = ttl_seconds
        self._cleanup_task: asyncio.Task | None = None
        self._running = False
    
    async def start(self) -> None:
        """Start the cache with periodic cleanup."""
        if self._running:
            return
            
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop the cache and cleanup resources."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clear all caches
        async with self._cache_lock:
            self._caches.clear()
        

    async def get_cache(self, execution_id: str) -> ExecutionCache:
        """Get or create a cache for an execution."""
        # Fast path: check if cache exists
        if execution_id in self._caches:
            return self._caches[execution_id]
        
        # Slow path: create cache with lock
        async with self._cache_lock:
            # Double-check after acquiring lock
            if execution_id not in self._caches:
                self._caches[execution_id] = ExecutionCache(execution_id)

            return self._caches[execution_id]
    
    async def remove_cache(self, execution_id: str) -> None:
        """Remove a cache for an execution."""
        async with self._cache_lock:
            if execution_id in self._caches:
                del self._caches[execution_id]

    async def get_dirty_caches(self) -> list[ExecutionCache]:
        """Get all caches with unpersisted changes."""
        async with self._cache_lock:
            return [
                cache for cache in self._caches.values()
                if cache.is_dirty()
            ]
    
    async def _cleanup_loop(self) -> None:
        """Periodically clean up expired caches."""
        cleanup_interval = min(300, self._ttl_seconds / 10)  # Check every 5 min or 10% of TTL
        
        while self._running:
            try:
                await asyncio.sleep(cleanup_interval)
                await self._cleanup_expired_caches()
            except asyncio.CancelledError:
                logger.debug("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
    
    async def _cleanup_expired_caches(self) -> None:
        """Remove caches that haven't been accessed recently."""
        current_time = time.time()
        expired_executions = []
        
        # Find expired caches
        async with self._cache_lock:
            for exec_id, cache in self._caches.items():
                if current_time - cache.get_last_access_time() > self._ttl_seconds:
                    if cache.is_dirty():
                        logger.warning(
                            f"Cache for execution {exec_id} has unpersisted changes "
                            f"but is being evicted due to TTL"
                        )
                    expired_executions.append(exec_id)
        
        # Remove expired caches
        for exec_id in expired_executions:
            await self.remove_cache(exec_id)

    
    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about the cache."""
        total_caches = len(self._caches)
        dirty_caches = sum(1 for cache in self._caches.values() if cache.is_dirty())
        
        return {
            "total_caches": total_caches,
            "dirty_caches": dirty_caches,
            "ttl_seconds": self._ttl_seconds,
        }