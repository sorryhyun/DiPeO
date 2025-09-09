"""Warm pool implementation for Claude Code SDK clients.

This approach maintains a pool of pre-warmed ClaudeSDKClient instances,
each used once then replaced, avoiding subprocess reuse issues.
"""

import asyncio
import contextlib
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient

logger = logging.getLogger(__name__)


@dataclass
class PoolStats:
    """Statistics for the warm pool."""

    total_created: int = 0
    total_borrowed: int = 0
    total_returned: int = 0
    current_size: int = 0
    current_available: int = 0
    failed_spawns: int = 0


class WarmPool:
    """Warm pool of Claude Code SDK clients.

    Maintains a pool of pre-connected clients. Each client is used
    once then closed and replaced with a fresh one.
    """

    def __init__(
        self,
        size: int,
        options: ClaudeCodeOptions,
        execution_phase: str = "default",
    ):
        """Initialize warm pool.

        Args:
            size: Number of clients to maintain in pool
            options: Claude Code options for all clients
            execution_phase: Execution phase for logging
        """
        self.size = size
        self.options = options
        self.execution_phase = execution_phase
        self.pool: deque[ClaudeSDKClient] = deque()
        self._lock = asyncio.Lock()
        self._started = False
        self._shutdown = False
        self._stats = PoolStats()
        self._spawn_tasks: set[asyncio.Task] = set()

        logger.info(f"[WarmPool] Initialized for {execution_phase}: size={size}")

    async def start(self) -> None:
        """Start the pool by pre-warming clients."""
        if self._started:
            return

        self._started = True
        logger.info(f"[WarmPool] Starting pool for {self.execution_phase}")

        # Pre-warm the pool
        tasks = []
        for _i in range(self.size):
            task = asyncio.create_task(self._spawn_one(initial=True))
            tasks.append(task)
            self._spawn_tasks.add(task)
            task.add_done_callback(self._spawn_tasks.discard)

        # Wait for initial pool to be ready
        await asyncio.gather(*tasks, return_exceptions=True)

        async with self._lock:
            self._stats.current_size = len(self.pool)
            self._stats.current_available = len(self.pool)

        logger.info(f"[WarmPool] Started with {self._stats.current_available} clients")

    async def _spawn_one(self, initial: bool = False) -> None:
        """Spawn a single client and add to pool.

        Args:
            initial: Whether this is part of initial pool creation
        """
        if self._shutdown:
            return

        try:
            # Create and connect client
            client = ClaudeSDKClient(options=self.options)
            await client.connect()

            async with self._lock:
                if not self._shutdown:
                    self.pool.append(client)
                    self._stats.total_created += 1
                    self._stats.current_size = len(self.pool)
                    self._stats.current_available = len(self.pool)

                    logger.debug(
                        f"[WarmPool] Spawned client for {self.execution_phase} "
                        f"(available: {self._stats.current_available})"
                    )
                else:
                    # Pool is shutting down, disconnect the client
                    try:
                        await client.disconnect()
                    except Exception as e:
                        # Ignore errors during shutdown
                        if "cancel scope" not in str(e).lower():
                            logger.debug(
                                f"[WarmPool] Error disconnecting client during shutdown: {e}"
                            )

        except Exception as e:
            self._stats.failed_spawns += 1
            logger.error(f"[WarmPool] Failed to spawn client for {self.execution_phase}: {e}")

            # If initial spawn fails, try again after a delay
            if initial and not self._shutdown:
                await asyncio.sleep(1)
                await self._spawn_one(initial=True)

    @contextlib.asynccontextmanager
    async def borrow(self):
        """Borrow a client from the pool.

        Yields:
            ClaudeSDKClient ready for use

        After use, the client is closed and a new one is spawned
        in the background to maintain pool size.
        """
        if not self._started:
            await self.start()

        # Wait for available client
        client = None
        attempts = 0
        max_attempts = 30  # 30 seconds timeout

        while client is None and attempts < max_attempts:
            async with self._lock:
                if self.pool:
                    client = self.pool.popleft()
                    self._stats.total_borrowed += 1
                    self._stats.current_available = len(self.pool)

                    logger.debug(
                        f"[WarmPool] Borrowed client for {self.execution_phase} "
                        f"(available: {self._stats.current_available})"
                    )

            if client is None:
                # No client available, wait a bit
                await asyncio.sleep(1)
                attempts += 1

        if client is None:
            raise TimeoutError(f"[WarmPool] No client available after {max_attempts}s")

        try:
            yield client
        finally:
            # Disconnect the used client in a separate task to avoid cancel scope issues
            # The client was created in a different task, so we need to disconnect it
            # in its own task context to avoid "cancel scope in different task" errors
            async def disconnect_client():
                try:
                    await client.disconnect()
                except Exception as e:
                    # Ignore cancel scope errors - they're expected when disconnecting
                    # a client created in a different task
                    if "cancel scope" not in str(e).lower():
                        logger.warning(f"[WarmPool] Error disconnecting client: {e}")

            # Run disconnect in a separate task
            disconnect_task = asyncio.create_task(disconnect_client())
            with contextlib.suppress(Exception):
                await disconnect_task

            self._stats.total_returned += 1

            # Spawn replacement in background (don't wait)
            if not self._shutdown:
                task = asyncio.create_task(self._spawn_one())
                self._spawn_tasks.add(task)
                task.add_done_callback(self._spawn_tasks.discard)

    async def shutdown(self) -> None:
        """Shutdown the pool and close all clients."""
        logger.info(f"[WarmPool] Shutting down pool for {self.execution_phase}")
        self._shutdown = True

        # Cancel pending spawn tasks
        for task in self._spawn_tasks:
            task.cancel()

        # Wait for spawn tasks to complete
        if self._spawn_tasks:
            await asyncio.gather(*self._spawn_tasks, return_exceptions=True)

        # Close all clients in pool
        async with self._lock:
            disconnect_tasks = []
            while self.pool:
                client = self.pool.popleft()

                # Create a task to disconnect each client to avoid cancel scope issues
                async def disconnect_client(c=client):
                    try:
                        await c.disconnect()
                    except Exception as e:
                        # Ignore cancel scope errors
                        if "cancel scope" not in str(e).lower():
                            logger.warning(f"[WarmPool] Error disconnecting client: {e}")

                disconnect_tasks.append(asyncio.create_task(disconnect_client()))

            # Wait for all disconnect tasks to complete
            if disconnect_tasks:
                await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        logger.info(
            f"[WarmPool] Shutdown complete. Stats: "
            f"created={self._stats.total_created}, "
            f"borrowed={self._stats.total_borrowed}, "
            f"returned={self._stats.total_returned}, "
            f"failed={self._stats.failed_spawns}"
        )

    def get_stats(self) -> dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary with pool stats
        """
        return {
            "execution_phase": self.execution_phase,
            "pool_size": self.size,
            "current_available": self._stats.current_available,
            "total_created": self._stats.total_created,
            "total_borrowed": self._stats.total_borrowed,
            "total_returned": self._stats.total_returned,
            "failed_spawns": self._stats.failed_spawns,
        }


class WarmPoolManager:
    """Manager for multiple warm pools keyed by execution phase."""

    def __init__(self, default_size: int = 2):
        """Initialize pool manager.

        Args:
            default_size: Default pool size for each phase
        """
        self.default_size = default_size
        self.pools: dict[str, WarmPool] = {}
        self._lock = asyncio.Lock()

        logger.info(f"[WarmPoolManager] Initialized with default size={default_size}")

    async def get_pool(
        self,
        options: ClaudeCodeOptions,
        execution_phase: str = "default",
        pool_size: int | None = None,
    ) -> WarmPool:
        """Get or create a warm pool for the given phase.

        Args:
            options: Claude Code options
            execution_phase: Execution phase key
            pool_size: Optional pool size override

        Returns:
            WarmPool instance
        """
        key = f"{execution_phase}:{hash(str(options.system_prompt))}"

        async with self._lock:
            if key not in self.pools:
                size = pool_size or self.default_size
                pool = WarmPool(size, options, execution_phase)
                await pool.start()
                self.pools[key] = pool
                logger.info(
                    f"[WarmPoolManager] Created pool for {execution_phase} " f"with size={size}"
                )

            return self.pools[key]

    async def shutdown_all(self) -> None:
        """Shutdown all pools."""
        logger.info("[WarmPoolManager] Shutting down all pools")

        async with self._lock:
            tasks = [pool.shutdown() for pool in self.pools.values()]
            await asyncio.gather(*tasks, return_exceptions=True)
            self.pools.clear()

        logger.info("[WarmPoolManager] All pools shut down")

    def get_all_stats(self) -> dict[str, Any]:
        """Get statistics for all pools.

        Returns:
            Dictionary with stats for each pool
        """
        return {
            "pools": [pool.get_stats() for pool in self.pools.values()],
            "total_pools": len(self.pools),
        }


# Global pool manager instance
_global_manager: WarmPoolManager | None = None
_manager_lock = asyncio.Lock()


async def get_global_manager() -> WarmPoolManager:
    """Get the global pool manager, creating if needed.

    Returns:
        Global WarmPoolManager instance
    """
    global _global_manager

    async with _manager_lock:
        if _global_manager is None:
            _global_manager = WarmPoolManager()
            logger.info("[WarmPoolManager] Created global manager")

        return _global_manager


async def shutdown_global_manager() -> None:
    """Shutdown the global pool manager."""
    global _global_manager

    async with _manager_lock:
        if _global_manager is not None:
            await _global_manager.shutdown_all()
            _global_manager = None
            logger.info("[WarmPoolManager] Global manager shut down")
