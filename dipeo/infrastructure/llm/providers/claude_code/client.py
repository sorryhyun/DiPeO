"""Claude Code client wrapper implementation using claude-code-sdk.

This module provides efficient query execution with optional session pooling
for improved performance when making multiple queries with the same system prompt.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Session pooling configuration
SESSION_POOL_ENABLED = os.getenv("DIPEO_SESSION_POOL_ENABLED", "false").lower() == "true"

logger.info(f"[ClaudeCode] Configuration: SESSION_POOL_ENABLED={SESSION_POOL_ENABLED}")


class QueryClientWrapper:
    """Wrapper around SDK's query() function with optional session pool support.

    This wrapper provides efficient query execution with automatic pooling:
    - Session pooling: When enabled and system_prompt provided, maintains connected sessions
    - Default: Falls back to SDK's default transport when pooling is disabled or unavailable
    """

    def __init__(
        self,
        options: Any,
        execution_phase: str = "default",
    ):
        """Initialize the query wrapper.

        Args:
            options: ClaudeCodeOptions for the query (may include system_prompt)
            execution_phase: Execution phase for pool key determination
        """
        self.options = options
        self.execution_phase = execution_phase
        self._wrapper = None

    async def __aenter__(self):
        """Enter context - create appropriate wrapper based on configuration."""
        # Try session pooling if enabled and system prompt is in options
        # Note: Pooling is disabled for direct_execution phase to avoid file watcher accumulation
        if (
            SESSION_POOL_ENABLED
            and hasattr(self.options, "system_prompt")
            and self.options.system_prompt
            # and (str(self.execution_phase or "").lower() not in {"direct_execution"})
        ):
            try:
                from .transport.session_wrapper import SessionQueryWrapper

                self._wrapper = SessionQueryWrapper(
                    options=self.options,
                    execution_phase=self.execution_phase,
                )
                await self._wrapper.__aenter__()
                logger.debug(
                    f"[QueryClientWrapper] Using session pool for {self.execution_phase} "
                    f"with system prompt from options"
                )
            except Exception as e:
                logger.warning(f"[QueryClientWrapper] Failed to initialize session pool: {e}")
                self._wrapper = None
        else:
            reason = "pooling disabled or no system prompt"
            if str(self.execution_phase or "").lower() == "direct_execution":
                reason = (
                    "direct_execution phase (pooling disabled to prevent file watcher accumulation)"
                )
            logger.debug(f"[QueryClientWrapper] Using default transport ({reason})")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context - cleanup session wrapper if used."""
        if self._wrapper:
            try:
                await self._wrapper.__aexit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                logger.error(f"[QueryClientWrapper] Error releasing session wrapper: {e}")
            self._wrapper = None

    async def query(self, prompt: str):
        """Execute query using session pool or default transport.

        Args:
            prompt: The prompt to send

        Yields:
            Messages from the query response
        """
        if self._wrapper:
            # Use session pool wrapper
            async for message in self._wrapper.query(prompt):
                yield message
        else:
            # Fall back to SDK's default query
            try:
                from claude_code_sdk import query
            except ImportError as e:
                logger.error("claude-code-sdk not installed")
                raise ImportError("claude-code-sdk is required") from e

            # Use default SDK query function
            logger.debug("[QueryClientWrapper] Using default transport")

            async for message in query(
                prompt=prompt,
                options=self.options,
                transport=None,  # Use default transport
            ):
                yield message

    async def force_cleanup(self):
        """Force cleanup of the session and subprocess on timeout.

        This is called when a query times out to ensure proper cleanup.
        """
        if self._wrapper and hasattr(self._wrapper, "force_cleanup"):
            await self._wrapper.force_cleanup()
        # If no wrapper or no force_cleanup method, just clean up normally
        elif self._wrapper:
            await self.__aexit__(None, None, None)
