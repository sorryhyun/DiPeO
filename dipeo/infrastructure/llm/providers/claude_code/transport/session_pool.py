"""Simplified session pooling for Claude Code SDK clients using fork_session.

This module provides a simplified session pooling mechanism that leverages the
fork_session feature to create fresh sessions from templates, eliminating the
need for complex state management and session reuse tracking.
"""

import asyncio
import logging

from dipeo.config.base_logger import get_module_logger
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from claude_code_sdk import ClaudeAgentOptions, ClaudeSDKClient

logger = get_module_logger(__name__)

# Session pool configuration
SESSION_POOL_ENABLED = os.getenv("DIPEO_SESSION_POOL_ENABLED", "false").lower() == "true"
SESSION_CONNECTION_TIMEOUT = float(os.getenv("DIPEO_SESSION_CONNECTION_TIMEOUT", "30"))

# fork_session feature detection
FORK_SESSION_SUPPORTED = "fork_session" in getattr(ClaudeAgentOptions, "__dataclass_fields__", {})

FORK_SESSION_ENABLED = FORK_SESSION_SUPPORTED and SESSION_POOL_ENABLED

logger.info(
    f"[SessionPool] Configuration: ENABLED={SESSION_POOL_ENABLED}, "
    f"FORK_SUPPORTED={FORK_SESSION_SUPPORTED}, "
    f"FORK_ENABLED={FORK_SESSION_ENABLED}"
)

@dataclass
class SessionClient:
    """Simple wrapper for a ClaudeSDKClient with minimal state.

    No complex state tracking - just a client that can be used once and discarded.
    """

    client: ClaudeSDKClient
    options: ClaudeAgentOptions
    session_id: str
    created_at: datetime
    is_connected: bool = False

    async def connect(self) -> None:
        """Connect the client with empty initial stream."""
        if self.is_connected:
            return

        try:
            await self.client.connect(None)
            self.is_connected = True
            logger.debug(f"[SessionClient] Connected session {self.session_id}")
        except Exception as e:
            logger.error(f"[SessionClient] Failed to connect session {self.session_id}: {e}")
            raise

    async def query(self, prompt: str | AsyncIterator[dict[str, Any]]):
        """Execute a query on this session.

        Args:
            prompt: The prompt to send

        Yields:
            Messages from the response
        """
        if not self.is_connected:
            raise RuntimeError(f"Session {self.session_id} not connected")

        try:
            # Send the query
            await self.client.query(prompt, session_id=self.session_id)

            # Stream responses
            async for message in self.client.receive_messages():
                # Track if session was forked
                new_session_id = getattr(message, "session_id", None)
                if new_session_id and new_session_id != self.session_id:
                    logger.debug(
                        f"[SessionClient] Session forked from {self.session_id} to {new_session_id}"
                    )
                    self.session_id = new_session_id

                yield message

                # Check for completion
                if hasattr(message, "result"):
                    break
        except Exception as e:
            logger.error(f"[SessionClient] Query failed for session {self.session_id}: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect the client."""
        if not self.is_connected:
            return

        try:
            await self.client.disconnect()
            self.is_connected = False
            logger.debug(f"[SessionClient] Disconnected session {self.session_id}")
        except Exception as e:
            logger.warning(f"[SessionClient] Error disconnecting session {self.session_id}: {e}")

class SimplifiedSessionPool:
    """Simplified session pool using fork_session for fresh sessions.

    Pre-creates template sessions for each execution phase and forks
    from them for each query, ensuring clean session state without
    complex reuse management.
    """

    def __init__(self):
        """Initialize the simplified session pool."""
        self.template_sessions: dict[str, SessionClient] = {}
        self._lock = asyncio.Lock()
        self._closed = False

    async def get_or_create_template(
        self, options: ClaudeAgentOptions, execution_phase: str = "default"
    ) -> SessionClient:
        """Get or create a template session for the given phase.

        Args:
            options: Claude Code options with system prompt
            execution_phase: Execution phase identifier

        Returns:
            Template SessionClient (not for direct use, only for forking)
        """
        async with self._lock:
            # Check if template already exists
            if execution_phase in self.template_sessions:
                template = self.template_sessions[execution_phase]
                # Ensure template is still connected
                if not template.is_connected:
                    await template.connect()
                return template

            # Enable fork_session if supported
            if FORK_SESSION_ENABLED and getattr(options, "fork_session", None) is not True:
                options.fork_session = True
                logger.debug(
                    f"[SimplifiedSessionPool] Enabled fork_session for phase '{execution_phase}'"
                )

            # Create new template session
            session_id = execution_phase  # Use phase as session ID
            template = SessionClient(
                client=ClaudeSDKClient(options=options),
                options=options,
                session_id=session_id,
                created_at=datetime.now(),
            )

            # Connect the template (establishes system prompt)
            await template.connect()

            # Store template
            self.template_sessions[execution_phase] = template
            logger.info(
                f"[SimplifiedSessionPool] Created template session for phase '{execution_phase}'"
            )

            return template

    async def get_forked_session(
        self, options: ClaudeAgentOptions, execution_phase: str = "default"
    ) -> SessionClient:
        """Get a fresh forked session from template.

        Args:
            options: Claude Code options
            execution_phase: Execution phase

        Returns:
            Fresh SessionClient ready for one-time use
        """
        if self._closed:
            raise RuntimeError("Session pool is closed")

        # Get or create template
        template = await self.get_or_create_template(options, execution_phase)

        # If fork_session is not enabled, just return the template
        # (fallback to old behavior for compatibility)
        if not FORK_SESSION_ENABLED:
            logger.debug(
                "[SimplifiedSessionPool] fork_session not enabled, using template directly"
            )
            return template

        # Create a new client that will fork from the template
        # The fork happens automatically when we query with the template's session_id
        forked_session = SessionClient(
            client=ClaudeSDKClient(options=template.options),
            options=template.options,
            session_id=template.session_id,  # Start with template's ID, will change on fork
            created_at=datetime.now(),
        )

        # Connect the forked session
        await forked_session.connect()

        logger.debug(
            f"[SimplifiedSessionPool] Created forked session from template '{execution_phase}'"
        )

        return forked_session

    async def shutdown(self) -> None:
        """Shutdown the pool and disconnect all template sessions."""
        logger.info("[SimplifiedSessionPool] Shutting down session pool")
        self._closed = True

        async with self._lock:
            # Disconnect all template sessions
            for phase, template in self.template_sessions.items():
                try:
                    await template.disconnect()
                    logger.debug(
                        f"[SimplifiedSessionPool] Disconnected template for phase '{phase}'"
                    )
                except Exception as e:
                    logger.warning(
                        f"[SimplifiedSessionPool] Error disconnecting template '{phase}': {e}"
                    )

            self.template_sessions.clear()

        logger.info("[SimplifiedSessionPool] Session pool shutdown complete")

class SessionPoolManager:
    """Manager for the simplified session pool.

    Maintains a single SimplifiedSessionPool instance for all execution phases.
    """

    def __init__(self):
        """Initialize session pool manager."""
        self._pool = SimplifiedSessionPool()
        self._closed = False

    async def get_session(
        self, options: ClaudeAgentOptions, execution_phase: str = "default"
    ) -> SessionClient:
        """Get a fresh session for the given configuration.

        Args:
            options: Claude Code options
            execution_phase: Execution phase identifier

        Returns:
            Fresh SessionClient ready for use
        """
        if self._closed:
            raise RuntimeError("SessionPoolManager is closed")

        return await self._pool.get_forked_session(options, execution_phase)

    async def shutdown_all(self) -> None:
        """Shutdown the pool."""
        self._closed = True
        await self._pool.shutdown()
        logger.info("[SessionPoolManager] Manager shutdown complete")

# Global session pool manager
_global_session_manager: SessionPoolManager | None = None
_session_manager_lock = asyncio.Lock()

async def get_global_session_manager() -> SessionPoolManager:
    """Get the global session pool manager, creating if needed.

    Returns:
        Global SessionPoolManager instance
    """
    global _global_session_manager

    async with _session_manager_lock:
        if _global_session_manager is None:
            _global_session_manager = SessionPoolManager()
            logger.info("[SessionPoolManager] Created global session manager")

        return _global_session_manager

async def shutdown_global_session_manager() -> None:
    """Shutdown the global session pool manager."""
    global _global_session_manager

    async with _session_manager_lock:
        if _global_session_manager is not None:
            await _global_session_manager.shutdown_all()
            _global_session_manager = None
            logger.info("[SessionPoolManager] Global session manager shut down")
