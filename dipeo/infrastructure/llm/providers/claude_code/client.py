"""Claude Code client wrapper implementation using claude-code-sdk.

This module provides efficient query execution with optional warm pooling
for improved performance when making multiple queries with the same system prompt.
Uses a warm pool of pre-connected clients to avoid subprocess reuse issues.
"""

import logging
import os
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Feature flags
ENABLE_WARM_POOL = os.getenv("DIPEO_ENABLE_WARM_POOL", "true").lower() == "true"
USE_QUERY_MODE = os.getenv("DIPEO_USE_QUERY_MODE", "false").lower() == "true"
WARM_POOL_SIZE = int(os.getenv("DIPEO_WARM_POOL_SIZE", "2"))

logger.info(
    f"[ClaudeCode] Feature flags: ENABLE_WARM_POOL={ENABLE_WARM_POOL}, USE_QUERY_MODE={USE_QUERY_MODE}, POOL_SIZE={WARM_POOL_SIZE}"
)


class ClientType(Enum):
    """Types of specialized Claude Code clients."""

    DEFAULT = "default"
    MEMORY_SELECTION = "memory_selection"
    DIRECT_EXECUTION = "direct_execution"
    DECISION_EVALUATION = "decision_evaluation"


class QueryClientWrapper:
    """Wrapper around SDK's query() function with optional warm pool support.

    This wrapper provides efficient query execution with automatic warm pooling
    when enabled, falling back to SDK's default transport when pooling is disabled.
    Uses a warm pool of pre-connected clients to avoid subprocess reuse issues.
    """

    def __init__(self, options: Any, pool_key: str = "default", execution_phase: str | None = None):
        """Initialize the query wrapper.

        Args:
            options: ClaudeCodeOptions for the query
            pool_key: Key for transport pool (deprecated, use execution_phase)
            execution_phase: Execution phase for pool key determination
        """
        self.options = options
        self.pool_key = pool_key  # Keep for backward compatibility
        self.execution_phase = execution_phase or pool_key
        self._wrapper = None

    async def __aenter__(self):
        """Enter context - create warm pool wrapper if enabled."""
        if ENABLE_WARM_POOL:
            try:
                from .transport.warm_wrapper import WarmQueryWrapper

                self._wrapper = WarmQueryWrapper(
                    options=self.options,
                    execution_phase=self.execution_phase,
                    pool_size=WARM_POOL_SIZE,
                )
                await self._wrapper.__aenter__()
                logger.debug(
                    f"[QueryClientWrapper] Using warm pool (phase={self.execution_phase}, size={WARM_POOL_SIZE})"
                )
            except Exception as e:
                logger.warning(f"[QueryClientWrapper] Failed to initialize warm pool: {e}")
                self._wrapper = None
        else:
            logger.debug("[QueryClientWrapper] Warm pool disabled")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context - cleanup warm pool wrapper if used."""
        if self._wrapper:
            try:
                await self._wrapper.__aexit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                logger.error(f"[QueryClientWrapper] Error releasing warm pool wrapper: {e}")
            self._wrapper = None

    async def query(self, prompt: str):
        """Execute query using warm pool or default transport.

        Args:
            prompt: The prompt to send

        Yields:
            Messages from the query response
        """
        if self._wrapper:
            # Use warm pool wrapper
            async for message in self._wrapper.query(prompt):
                yield message
        else:
            # Fall back to SDK's default transport
            try:
                from claude_code_sdk import query
            except ImportError as e:
                logger.error("claude-code-sdk not installed")
                raise ImportError("claude-code-sdk is required") from e

            async for message in query(
                prompt=prompt,
                options=self.options,
                transport=None,  # Let SDK create SubprocessCLITransport
            ):
                yield message

    async def receive_messages(self):
        """Compatibility method for ClaudeSDKClient interface.

        This method should not be used with QueryClientWrapper.
        Use the query() method directly instead.
        """
        raise NotImplementedError(
            "QueryClientWrapper doesn't support receive_messages(). "
            "Use async for msg in wrapper.query(prompt) instead."
        )
