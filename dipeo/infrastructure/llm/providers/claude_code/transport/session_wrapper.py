"""Session wrapper for Claude Code queries with simplified pooling.

Provides SessionQueryWrapper that gets fresh sessions from the pool
for each query, leveraging fork_session for clean session state.
"""

import logging
from collections.abc import AsyncIterator
from typing import Any

from claude_code_sdk import ClaudeCodeOptions

from .session_pool import get_global_session_manager

logger = logging.getLogger(__name__)


class SessionQueryWrapper:
    """Wrapper that uses simplified session pooling for Claude Code queries.

    Gets fresh forked sessions from template sessions for each query,
    ensuring clean state without complex reuse management.
    """

    def __init__(
        self,
        options: ClaudeCodeOptions,
        execution_phase: str = "default",
    ):
        """Initialize session query wrapper.

        Args:
            options: Claude Code options (includes system_prompt)
            execution_phase: Execution phase for session selection
        """
        self.options = options
        self.execution_phase = execution_phase
        self._session = None

    async def __aenter__(self):
        """Enter context - get fresh session from pool."""
        # Get the global session manager
        manager = await get_global_session_manager()

        # Get a fresh session (forked from template if enabled)
        self._session = await manager.get_session(
            options=self.options,
            execution_phase=self.execution_phase,
        )

        # Log MCP server configuration if present
        if hasattr(self.options, "mcp_servers") and self.options.mcp_servers:
            logger.debug(
                f"[SessionQueryWrapper] Session {self._session.session_id} initialized with MCP servers: "
                f"{list(self.options.mcp_servers.keys())}, allowed_tools: {getattr(self.options, 'allowed_tools', [])}"
            )
        else:
            logger.debug(
                f"[SessionQueryWrapper] Session {self._session.session_id} initialized without MCP servers"
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context - disconnect and cleanup session."""
        if self._session:
            try:
                # Always disconnect the session - it's a one-time use session
                await self._session.disconnect()
            except Exception as e:
                logger.warning(
                    f"[SessionQueryWrapper] Error disconnecting session {self._session.session_id}: {e}"
                )
            finally:
                self._session = None

    async def query(self, prompt: str | AsyncIterator[dict[str, Any]]) -> AsyncIterator[Any]:
        """Execute query using the session.

        Args:
            prompt: The prompt to send (string or async iterable of message dicts)

        Yields:
            Messages from the query response
        """
        if not self._session:
            raise RuntimeError("SessionQueryWrapper not in context")

        try:
            # Execute query on the session
            message_count = 0
            async for message in self._session.query(prompt):
                message_count += 1
                yield message

            logger.debug(
                f"[SessionQueryWrapper] Query completed on session {self._session.session_id}, "
                f"received {message_count} messages"
            )

        except Exception as e:
            logger.error(
                f"[SessionQueryWrapper] Query failed on session {self._session.session_id}: {e}"
            )
            raise
