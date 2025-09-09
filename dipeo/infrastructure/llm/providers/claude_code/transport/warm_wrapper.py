"""Session pool wrapper for Claude Code queries.

Supports session-based pooling for memory selection and system prompt persistence.
Falls back to default SDK query when session pooling is disabled.
"""

import logging
from collections.abc import AsyncIterator
from typing import Any

from claude_code_sdk import ClaudeCodeOptions
from claude_code_sdk import query as sdk_query

from .session_pool import (
    SESSION_POOL_ENABLED,
    get_global_session_manager,
)

logger = logging.getLogger(__name__)


class SessionQueryWrapper:
    """Wrapper that uses session-based pooling for Claude Code queries.

    Maintains connected sessions with system prompt configured in options
    for efficient multi-query conversations with memory selection support.
    """

    def __init__(
        self,
        options: ClaudeCodeOptions,
        execution_phase: str = "default",
    ):
        """Initialize session query wrapper.

        Args:
            options: Claude Code options (includes system_prompt)
            execution_phase: Execution phase for pool key
        """
        self.options = options
        self.execution_phase = execution_phase
        self._session = None
        self._pool = None

    async def __aenter__(self):
        """Enter context - get session pool and borrow session."""
        # Get or create pool for this configuration
        manager = await get_global_session_manager()
        self._pool = await manager.get_or_create_pool(
            options=self.options,
            execution_phase=self.execution_phase,
        )

        # Borrow a session from the pool (will connect on-demand)
        self._session = await self._pool.borrow()

        logger.debug(
            f"[SessionQueryWrapper] Borrowed session {self._session.session_id} "
            f"for phase '{self.execution_phase}'"
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context - session automatically returns to pool."""
        # Sessions are automatically returned to pool (no explicit return needed)
        # They remain connected for reuse
        if self._session:
            logger.debug(
                f"[SessionQueryWrapper] Released session {self._session.session_id} "
                f"(queries: {self._session.query_count}/{self._session.max_queries})"
            )
            self._session = None

    async def query(self, prompt: str) -> AsyncIterator[Any]:
        """Execute query using session.

        Args:
            prompt: The prompt to send

        Yields:
            Messages from the query response
        """
        if not self._session:
            raise RuntimeError("SessionQueryWrapper not in context")

        try:
            # Execute query on the session
            async for message in self._session.query(prompt):
                yield message

        except Exception as e:
            logger.error(
                f"[SessionQueryWrapper] Query failed on session {self._session.session_id}: {e}"
            )
            raise


# Convenience function for single queries
async def warm_query(
    prompt: str,
    options: ClaudeCodeOptions,
    execution_phase: str = "default",
) -> str:
    """Execute a single query using session pool or default SDK.

    Args:
        prompt: The prompt to send
        options: Claude Code options (may include system_prompt)
        execution_phase: Execution phase for pool key

    Returns:
        The result text from the query
    """
    # Use session pooling if enabled and system prompt is in options
    if SESSION_POOL_ENABLED and hasattr(options, "system_prompt") and options.system_prompt:
        async with SessionQueryWrapper(options, execution_phase) as wrapper:
            result = ""
            async for message in wrapper.query(prompt):
                if hasattr(message, "result"):
                    result = message.result
                    break
            return result
    else:
        # Use default SDK query (no pooling)
        logger.debug(f"[warm_query] Using default SDK query for phase '{execution_phase}'")
        result = ""
        async for message in sdk_query(prompt, options):
            if hasattr(message, "result"):
                result = message.result
                break
        return result
