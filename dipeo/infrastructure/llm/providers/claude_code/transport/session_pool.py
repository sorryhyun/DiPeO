"""Session-based pooling for Claude Code SDK clients.

This module provides session-based client pooling that maintains connected
ClaudeSDKClient instances across multiple queries, enabling memory selection
and system prompt persistence while avoiding subprocess reuse issues.
"""

import asyncio
import contextlib
import logging
import os
import time
from collections import OrderedDict
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient

logger = logging.getLogger(__name__)

# Session pool configuration
SESSION_POOL_ENABLED = os.getenv("DIPEO_SESSION_POOL_ENABLED", "false").lower() == "true"
SESSION_REUSE_LIMIT = int(os.getenv("DIPEO_SESSION_REUSE_LIMIT", "5"))
SESSION_IDLE_TTL = float(os.getenv("DIPEO_SESSION_IDLE_TTL", "30"))  # seconds
SESSION_MAX_POOLS = int(os.getenv("DIPEO_SESSION_MAX_POOLS", "5"))
SESSION_CONNECTION_TIMEOUT = float(os.getenv("DIPEO_SESSION_CONNECTION_TIMEOUT", "30"))
SESSION_GRACE_PERIOD = float(
    os.getenv("DIPEO_SESSION_GRACE_PERIOD", "3")
)  # Grace period after query completion
SESSION_DISCONNECT_GRACE = float(os.getenv("DIPEO_SESSION_DISCONNECT_GRACE", "0.25"))
SESSION_TERM_TIMEOUT = float(os.getenv("DIPEO_SESSION_TERM_TIMEOUT", "2.0"))

logger.info(
    f"[SessionPool] Configuration: ENABLED={SESSION_POOL_ENABLED}, "
    f"REUSE_LIMIT={SESSION_REUSE_LIMIT}, IDLE_TTL={SESSION_IDLE_TTL}s, "
    f"MAX_POOLS={SESSION_MAX_POOLS}"
)


@dataclass
class SessionStats:
    """Statistics for a session pool."""

    total_created: int = 0
    total_borrowed: int = 0
    total_queries: int = 0
    total_reused: int = 0
    expired_sessions: int = 0
    failed_creates: int = 0
    avg_queries_per_session: float = 0.0


@dataclass
class SessionClient:
    """Wrapper for a connected ClaudeSDKClient with session state.

    Maintains a persistent connection to Claude with system prompt configured
    in ClaudeCodeOptions and supports multiple queries through the same connection.
    """

    client: ClaudeSDKClient
    options: ClaudeCodeOptions
    session_id: str
    created_at: datetime
    last_used_at: datetime | None = None
    query_count: int = 0
    max_queries: int = SESSION_REUSE_LIMIT
    is_connected: bool = False
    is_busy: bool = False
    subprocess_pid: int | None = None
    owner_task: asyncio.Task | None = None
    is_reserved: bool = False

    def reserve(self) -> None:
        """Reserve the session so it cannot be borrowed concurrently."""
        if self.is_busy:
            raise RuntimeError(f"Session {self.session_id} is already processing a query")
        if self.is_reserved:
            raise RuntimeError(f"Session {self.session_id} is already reserved")
        self.is_reserved = True

    def release_reservation(self) -> None:
        """Release any pending reservation on the session."""
        self.is_reserved = False

    async def connect(self) -> None:
        """Connect the client with None (empty initial stream).

        The system prompt is already configured in ClaudeCodeOptions.
        """
        if self.is_connected:
            return

        try:
            # Connect with None - system prompt is in options
            await self.client.connect(None)
            self.is_connected = True
            self.last_used_at = datetime.now()
            self.owner_task = asyncio.current_task()
            self.is_reserved = False

            # Store the subprocess PID for targeted cleanup
            if hasattr(self.client, "_transport") and hasattr(self.client._transport, "_process"):
                try:
                    self.subprocess_pid = self.client._transport._process.pid
                except Exception as e:
                    logger.debug(f"[SessionClient] Could not get subprocess PID: {e}")

        except Exception as e:
            logger.error(f"[SessionClient] Failed to connect session {self.session_id}: {e}")
            raise

    async def query(self, prompt: str | AsyncIterator[dict[str, Any]]):
        """Execute a query on this session.

        Args:
            prompt: The prompt to send (string or async iterable of message dicts)

        Yields:
            Messages from the response
        """
        if not self.is_connected:
            raise RuntimeError(f"Session {self.session_id} not connected")

        if self.is_busy:
            raise RuntimeError(f"Session {self.session_id} is already processing a query")

        # Update timestamp immediately when query starts (before marking busy)
        self.last_used_at = datetime.now()
        # Reservation is no longer needed once the query starts
        self.is_reserved = False
        self.is_busy = True
        self.query_count += 1

        try:
            # Send the query
            await self.client.query(prompt, session_id=self.session_id)

            # Stream responses with cancellation support
            try:
                async for message in self.client.receive_messages():
                    yield message

                    # Check for completion
                    if hasattr(message, "result"):
                        break
            except asyncio.CancelledError:
                logger.warning(
                    f"[SessionClient] Query cancelled for session {self.session_id} (query {self.query_count})"
                )
                # Re-raise to propagate cancellation
                raise

        finally:
            self.is_busy = False
            # Update timestamp after query completes
            self.last_used_at = datetime.now()
            # Ensure reservation flag is cleared after query completion
            self.is_reserved = False

    async def disconnect(self) -> None:
        """Disconnect the client with timeout protection and task verification."""
        if not self.is_connected:
            return

        # Only allow graceful disconnect from the same task that did connect()
        same_task = self.owner_task is None or asyncio.current_task() is self.owner_task
        if same_task:
            try:
                await asyncio.wait_for(self.client.disconnect(), timeout=SESSION_DISCONNECT_GRACE)
                self.is_connected = False
                self.is_reserved = False
                return
            except TimeoutError:
                logger.warning(
                    f"[SessionClient] Disconnect timed out for session {self.session_id}"
                )
                # Fall through to raise error
            except Exception as e:
                logger.warning(
                    f"[SessionClient] Error disconnecting session {self.session_id}: {e}"
                )
                # Fall through to raise error

        # Different task or timed out - let force_disconnect handle kill
        raise RuntimeError("Skip graceful disconnect (task mismatch or timeout)")

    async def force_disconnect(self) -> None:
        """Force disconnect gracefully: SDK disconnect → SIGTERM (wait) → SIGKILL."""
        import psutil

        # Check if we should proceed with disconnect
        if self.is_busy:
            logger.warning(
                f"[SessionClient] Attempted to force disconnect busy session {self.session_id} - skipping"
            )
            return

        logger.warning(
            f"[SessionClient] Force disconnecting session {self.session_id} "
            f"(connected={self.is_connected}, queries={self.query_count}/{self.max_queries})"
        )

        # Best-effort graceful disconnect (may have already failed above)
        try:
            await self.disconnect()
        except Exception as e:
            # Expected if task mismatch or timeout - proceed to kill
            logger.debug(f"[SessionClient] Graceful disconnect skipped: {e}")

        killed = False

        pid = getattr(self, "subprocess_pid", None)
        if pid:
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    # Verify this is still our subprocess before terminating
                    term_timeout = SESSION_TERM_TIMEOUT
                    kill_pg = os.getenv("DIPEO_SESSION_KILL_PG", "false").lower() == "true"
                    logger.warning(
                        f"[SessionClient] Terminating PID {pid} for session {self.session_id} "
                        f"(timeout={term_timeout}s)"
                    )
                    try:
                        if kill_pg and hasattr(os, "killpg"):
                            import os as _os
                            import signal

                            _os.killpg(_os.getpgid(pid), signal.SIGTERM)
                        else:
                            proc.terminate()
                        proc.wait(timeout=term_timeout)
                    except psutil.TimeoutExpired:
                        logger.warning(f"[SessionClient] PID {pid} didn't exit; sending SIGKILL")
                        if kill_pg and hasattr(os, "killpg"):
                            import os as _os
                            import signal

                            _os.killpg(_os.getpgid(pid), signal.SIGKILL)
                        else:
                            proc.kill()
                        killed = True
                    except Exception as e:
                        logger.debug(f"[SessionClient] terminate() raised: {e}; killing")
                        proc.kill()
                        killed = True
            except psutil.NoSuchProcess:
                logger.debug(f"[SessionClient] Subprocess PID {pid} no longer exists")
            except psutil.AccessDenied:
                logger.warning(f"[SessionClient] Access denied to control PID {pid}")
            except Exception as e:
                logger.warning(f"[SessionClient] Error handling PID {pid}: {e}")

        self.is_connected = False
        self.is_reserved = False

    def can_reuse(self) -> bool:
        """Check if this session can be reused for another query."""
        if not self.is_connected or self.is_busy or self.is_reserved:
            return False

        # Check query limit
        if self.query_count >= self.max_queries:
            return False

        # Check idle timeout
        idle_time = (datetime.now() - self.last_used_at).total_seconds()
        if idle_time > SESSION_IDLE_TTL:
            return False

        return True

    def is_expired(self) -> bool:
        """Check if this session has expired."""
        # Never mark busy sessions as expired - they're actively processing
        if self.is_busy:
            return False

        # Check idle timeout only for non-busy sessions
        # Add grace period to prevent cleanup immediately after query completion
        idle_time = (datetime.now() - self.last_used_at).total_seconds()
        return idle_time > (SESSION_IDLE_TTL + SESSION_GRACE_PERIOD)


class SessionPool:
    """Pool of session clients for a specific configuration.

    Maintains a pool of SessionClient instances that can be reused
    for multiple queries with the same system prompt (configured in options).
    Clients are connected on-demand when borrowed.
    """

    def __init__(
        self,
        options: ClaudeCodeOptions,
        pool_key: str,
        max_sessions: int = 2,
    ):
        """Initialize session pool.

        Args:
            options: Claude Code options (includes system_prompt)
            pool_key: Unique key for this pool
            max_sessions: Maximum number of sessions to maintain
        """
        self.options = options
        self.pool_key = pool_key
        self.max_sessions = max_sessions
        self._sessions: list[SessionClient] = []
        self._stats = SessionStats()
        self._lock = asyncio.Lock()
        self._closed = False
        self._pending_cleanup: list[SessionClient] = []  # Sessions pending cleanup

    async def borrow(self) -> SessionClient:
        """Borrow a session from the pool, creating and connecting if necessary.

        Returns:
            A connected SessionClient ready for queries
        """
        if self._closed:
            raise RuntimeError(f"Pool '{self.pool_key}' is closed")

        # Collect sessions to clean up while holding lock
        pending_cleanup = []
        session_to_return = None

        async with self._lock:
            # Clean up expired and non-reusable sessions
            await self._cleanup_expired()
            await self._cleanup_unusable()

            # Move pending cleanup to local list and clear
            pending_cleanup = self._pending_cleanup[:]
            self._pending_cleanup.clear()

            # Find an available session
            for session in self._sessions:
                if session.can_reuse():
                    # Ensure session is connected
                    if not session.is_connected:
                        await session.connect()

                    try:
                        session.reserve()
                    except RuntimeError:
                        # Another borrower reserved between checks; skip
                        continue

                    self._stats.total_borrowed += 1
                    self._stats.total_reused += 1
                    session_to_return = session
                    break

            # Create new session if under limit and no session found
            if not session_to_return and len(self._sessions) < self.max_sessions:
                session = await self._create_session()
                # Connect the session before returning
                await session.connect()
                session.reserve()
                self._sessions.append(session)
                self._stats.total_borrowed += 1
                session_to_return = session

        # Cleanup outside the lock
        for session in pending_cleanup:
            try:
                await session.force_disconnect()
            except Exception as e:
                logger.debug(f"[SessionPool] Error during pending cleanup: {e}")

        if session_to_return:
            return session_to_return

        # No available sessions and at limit
        raise RuntimeError(
            f"No available sessions in pool '{self.pool_key}' "
            f"({len(self._sessions)}/{self.max_sessions} sessions)"
        )

    async def _create_session(self) -> SessionClient:
        """Create a new session client (not yet connected).

        Returns:
            A new SessionClient instance (unconnected)
        """
        try:
            # Use pool key directly as session ID for consistency across runs
            # This ensures memory_selection, decision_evaluation, and direct_execution
            # always have the same session IDs
            session_id = self.pool_key

            # Create session client (not connected yet)
            session = SessionClient(
                client=ClaudeSDKClient(options=self.options),
                options=self.options,
                session_id=session_id,
                created_at=datetime.now(),
            )

            self._stats.total_created += 1

            return session

        except Exception as e:
            self._stats.failed_creates += 1
            logger.error(f"[SessionPool] Failed to create session for pool '{self.pool_key}': {e}")
            raise

    async def _cleanup_expired(self) -> None:
        """Remove expired sessions from the pool."""
        expired = []
        active = []

        for session in self._sessions:
            # Double-check: Never clean up busy sessions even if marked as expired
            if session.is_expired() and not session.is_busy:
                expired.append(session)
                self._stats.expired_sessions += 1
            else:
                active.append(session)

        self._sessions = active

        # Add expired sessions to pending cleanup list
        for session in expired:
            self._pending_cleanup.append(session)

    async def _cleanup_unusable(self) -> None:
        """Remove sessions that can no longer be reused from the pool."""
        unusable = []
        active = []

        for session in self._sessions:
            # Remove sessions that are not busy but can't be reused (e.g., reached max queries)
            if session.is_reserved:
                active.append(session)
                continue

            if not session.is_busy and not session.can_reuse():
                unusable.append(session)
            else:
                active.append(session)

        self._sessions = active

        # Add unusable sessions to pending cleanup list
        for session in unusable:
            self._pending_cleanup.append(session)

    async def _disconnect_session(self, session: SessionClient) -> None:
        """Disconnect a session safely."""
        try:
            await session.disconnect()
        except Exception as e:
            logger.warning(f"[SessionPool] Error disconnecting session {session.session_id}: {e}")

    async def remove_session(self, session: SessionClient) -> None:
        """Remove a specific session from the pool (e.g., on timeout)."""
        async with self._lock:
            if session in self._sessions:
                self._sessions.remove(session)
                logger.warning(
                    f"[SessionPool] Forcefully removed session {session.session_id} from pool '{self.pool_key}' "
                    f"(was_busy={session.is_busy}, query_count={session.query_count})"
                )
                # Mark session as not busy to allow force disconnect
                session.is_busy = False
                # Force disconnect to ensure subprocess is killed
                await session.force_disconnect()
            else:
                logger.debug(
                    f"[SessionPool] Session {session.session_id} not found in pool '{self.pool_key}' "
                    f"(may have been already cleaned up)"
                )

    async def shutdown(self) -> None:
        """Shutdown the pool and disconnect all sessions."""
        logger.info(f"[SessionPool] Shutting down pool '{self.pool_key}'")
        self._closed = True

        async with self._lock:
            # Disconnect all sessions
            for session in self._sessions:
                await self._disconnect_session(session)

            # Clean up pending sessions
            for session in self._pending_cleanup:
                await session.force_disconnect()

            self._sessions.clear()
            self._pending_cleanup.clear()

        # Calculate final stats
        if self._stats.total_created > 0:
            self._stats.avg_queries_per_session = (
                self._stats.total_queries / self._stats.total_created
            )

        logger.info(
            f"[SessionPool] Pool '{self.pool_key}' shutdown. Stats: "
            f"created={self._stats.total_created}, "
            f"reused={self._stats.total_reused}, "
            f"expired={self._stats.expired_sessions}, "
            f"avg_queries={self._stats.avg_queries_per_session:.1f}"
        )

    def get_stats(self) -> dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary with pool stats
        """
        return {
            "pool_key": self.pool_key,
            "active_sessions": len(self._sessions),
            "max_sessions": self.max_sessions,
            "total_created": self._stats.total_created,
            "total_borrowed": self._stats.total_borrowed,
            "total_reused": self._stats.total_reused,
            "expired_sessions": self._stats.expired_sessions,
            "failed_creates": self._stats.failed_creates,
            "avg_queries_per_session": round(self._stats.avg_queries_per_session, 2),
        }


class SessionPoolManager:
    """Manager for multiple session pools keyed by configuration.

    Uses LRU eviction to prevent unbounded pool growth.
    """

    def __init__(self, max_pools: int = SESSION_MAX_POOLS):
        """Initialize session pool manager.

        Args:
            max_pools: Maximum number of pools to maintain
        """
        self.max_pools = max_pools
        self._pools: OrderedDict[str, SessionPool] = OrderedDict()
        self._lock = asyncio.Lock()
        self._closed = False

    def _generate_pool_key(
        self,
        execution_phase: str,
        options: ClaudeCodeOptions,
    ) -> str:
        """Generate a pool key based on execution phase.

        Simply use the execution phase name directly for all cases,
        ensuring consistent session IDs across diagram runs.

        Args:
            execution_phase: The execution phase
            options: Claude Code options (unused, kept for compatibility)

        Returns:
            The execution phase as the pool key
        """
        return execution_phase

    async def get_or_create_pool(
        self,
        options: ClaudeCodeOptions,
        execution_phase: str = "default",
    ) -> SessionPool:
        """Get or create a session pool for the given configuration.

        Args:
            options: Claude Code options (includes system_prompt)
            execution_phase: Execution phase identifier

        Returns:
            SessionPool instance
        """
        if self._closed:
            raise RuntimeError("SessionPoolManager is closed")

        # Generate pool key based on phase and system prompt in options
        pool_key = self._generate_pool_key(execution_phase, options)

        async with self._lock:
            # Check if pool exists (LRU update)
            if pool_key in self._pools:
                pool = self._pools.pop(pool_key)
                self._pools[pool_key] = pool  # Move to end (most recent)
                return pool

            # Evict LRU pool if at limit
            if len(self._pools) >= self.max_pools:
                evict_key, evicted = self._pools.popitem(last=False)
                logger.info(f"[SessionPoolManager] Evicting LRU pool '{evict_key}'")
                # Shutdown evicted pool directly (await instead of background task)
                await evicted.shutdown()

            # Create new pool
            # Since we use pool_key as session_id directly, limit to 1 session per pool
            pool = SessionPool(
                options=options,
                pool_key=pool_key,
                max_sessions=1,  # One session per pool for consistent session IDs
            )
            self._pools[pool_key] = pool

            return pool

    async def shutdown_all(self) -> None:
        """Shutdown all pools."""
        self._closed = True

        async with self._lock:
            # Shutdown all pools
            for key, pool in list(self._pools.items()):
                try:
                    await pool.shutdown()
                except Exception as e:
                    logger.error(f"[SessionPoolManager] Error shutting down pool '{key}': {e}")

            self._pools.clear()

        logger.info("[SessionPoolManager] All session pools shut down")

    def get_all_stats(self) -> dict[str, Any]:
        """Get statistics for all pools.

        Returns:
            Dictionary with stats for each pool
        """
        return {
            "pools": [pool.get_stats() for pool in self._pools.values()],
            "total_pools": len(self._pools),
            "max_pools": self.max_pools,
        }


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
