"""Session wrapper for Claude Code queries with pooling support.

Provides SessionQueryWrapper that manages session lifecycle from the session pool,
enabling efficient reuse of connected sessions for multiple queries with the same
system prompt configuration.
"""

import logging
from collections.abc import AsyncIterator
from typing import Any

from claude_code_sdk import ClaudeCodeOptions

from .session_pool import get_global_session_manager

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

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context - clean up non-reusable sessions in same context."""
        if self._session:
            # If the session cannot be reused (reached REUSE_LIMIT) or is expired,
            # remove it here so disconnect runs in the same task that used it.
            try:
                if (not self._session.can_reuse()) or self._session.is_expired():
                    await self._pool.remove_session(self._session)
            finally:
                self._session = None

    async def force_cleanup(self):
        """Force cleanup of the session and its subprocess on timeout."""
        if self._session:
            logger.warning(
                f"[SessionQueryWrapper] Force cleanup of session {self._session.session_id}"
            )
            # Force disconnect the session (this should kill the subprocess)
            await self._session.force_disconnect()

            # Remove session from pool if possible
            if self._pool:
                await self._pool.remove_session(self._session)

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
