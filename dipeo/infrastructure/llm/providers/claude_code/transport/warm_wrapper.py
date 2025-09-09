"""Warm pool wrapper for Claude Code queries.

Uses WarmPool to maintain pre-connected clients, avoiding subprocess reuse issues.
"""

import logging
from collections.abc import AsyncIterator
from typing import Any

from claude_code_sdk import ClaudeCodeOptions

from .warm_pool import get_global_manager

logger = logging.getLogger(__name__)


class WarmQueryWrapper:
    """Wrapper that uses warm pool for Claude Code queries.

    Each query gets a fresh client from the pool, avoiding
    subprocess reuse issues while maintaining performance benefits.
    """

    def __init__(
        self,
        options: ClaudeCodeOptions,
        execution_phase: str = "default",
        pool_size: int = 2,
    ):
        """Initialize warm query wrapper.

        Args:
            options: Claude Code options
            execution_phase: Execution phase for pool key
            pool_size: Size of warm pool
        """
        self.options = options
        self.execution_phase = execution_phase
        self.pool_size = pool_size
        self._pool = None
        self._client = None

        logger.debug(
            f"[WarmQueryWrapper] Created for phase={execution_phase}, " f"pool_size={pool_size}"
        )

    async def __aenter__(self):
        """Enter context - get pool and borrow client."""
        # Get or create pool for this phase
        manager = await get_global_manager()
        self._pool = await manager.get_pool(self.options, self.execution_phase, self.pool_size)

        # Borrow a client from the pool
        self._client_context = self._pool.borrow()
        self._client = await self._client_context.__aenter__()

        logger.debug(
            f"[WarmQueryWrapper] Acquired client from pool " f"(phase={self.execution_phase})"
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context - return client to pool."""
        if self._client_context:
            await self._client_context.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None
            self._client_context = None

            logger.debug(
                f"[WarmQueryWrapper] Released client to pool " f"(phase={self.execution_phase})"
            )

    async def query(self, prompt: str) -> AsyncIterator[Any]:
        """Execute query using warm client.

        Args:
            prompt: The prompt to send

        Yields:
            Messages from the query response
        """
        if not self._client:
            raise RuntimeError("WarmQueryWrapper not in context")

        logger.debug(f"[WarmQueryWrapper] Executing query " f"(phase={self.execution_phase})")

        try:
            # Send the query
            await self._client.query(prompt, session_id="default")

            # Stream responses
            async for message in self._client.receive_response():
                yield message

                # Check for completion
                if hasattr(message, "result"):
                    logger.debug(
                        f"[WarmQueryWrapper] Query completed " f"(phase={self.execution_phase})"
                    )
                    break

        except Exception as e:
            logger.error(f"[WarmQueryWrapper] Query failed " f"(phase={self.execution_phase}): {e}")
            raise


# Convenience function for single queries
async def warm_query(
    prompt: str,
    options: ClaudeCodeOptions,
    execution_phase: str = "default",
) -> str:
    """Execute a single query using warm pool.

    Args:
        prompt: The prompt to send
        options: Claude Code options
        execution_phase: Execution phase for pool key

    Returns:
        The result text from the query
    """
    async with WarmQueryWrapper(options, execution_phase) as wrapper:
        result = ""
        async for message in wrapper.query(prompt):
            if hasattr(message, "result"):
                result = message.result
                break
        return result
