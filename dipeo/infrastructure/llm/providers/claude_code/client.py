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

# Deprecated environment variables (kept for backward compatibility warnings)
# These are no longer used but we check them to warn users
_DEPRECATED_ENV_VARS = {
    "DIPEO_ENABLE_WARM_POOL": "Warm pooling has been removed. Use session pooling instead.",
    "DIPEO_WARM_POOL_SIZE": "Warm pool size configuration has been removed.",
    "DIPEO_CONNECTED_TRANSPORT": "Connected transport has been removed.",
    "DIPEO_CONNECTED_REUSE": "Connected transport configuration has been removed.",
    "DIPEO_CONNECTED_IDLE_TTL": "Connected transport configuration has been removed.",
    "DIPEO_USE_QUERY_MODE": "Query mode flag has been removed.",
}

# Check for deprecated environment variables and warn
for env_var, message in _DEPRECATED_ENV_VARS.items():
    if os.getenv(env_var):
        logger.warning(f"[ClaudeCode] DEPRECATED: {env_var} is no longer used. {message}")

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
        pool_key: str = "default",
        execution_phase: str | None = None,
    ):
        """Initialize the query wrapper.

        Args:
            options: ClaudeCodeOptions for the query (may include system_prompt)
            pool_key: Key for transport pool (deprecated, use execution_phase)
            execution_phase: Execution phase for pool key determination
        """
        self.options = options
        self.pool_key = pool_key  # Keep for backward compatibility
        self.execution_phase = execution_phase or pool_key
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
                from .transport.warm_wrapper import SessionQueryWrapper

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

    async def receive_messages(self):
        """Compatibility method for ClaudeSDKClient interface.

        This method should not be used with QueryClientWrapper.
        Use the query() method directly instead.
        """
        raise NotImplementedError(
            "QueryClientWrapper doesn't support receive_messages(). "
            "Use async for msg in wrapper.query(prompt) instead."
        )
