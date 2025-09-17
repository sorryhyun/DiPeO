"""TodoSyncService for live synchronization of TODO updates to diagrams."""

import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from dipeo.domain.diagram.services.todo_translator import TodoTranslator
from dipeo.infrastructure.llm.providers.claude_code.todo_collector import TodoSnapshot

logger = logging.getLogger(__name__)


class TodoSyncMode(Enum):
    """Synchronization mode for TODO updates."""

    OFF = "off"  # No synchronization
    MANUAL = "manual"  # Manual trigger only
    AUTO = "auto"  # Automatic with debouncing
    WATCH = "watch"  # Watch mode with file monitoring


@dataclass
class TodoSyncConfig:
    """Configuration for TODO synchronization."""

    mode: TodoSyncMode = TodoSyncMode.OFF
    debounce_seconds: float = 2.0  # Coalesce rapid updates
    persistence_path: Path = field(default_factory=lambda: Path("projects/dipeo_cc"))
    auto_execute: bool = False  # Automatically run generated diagrams
    monitor_enabled: bool = True  # Enable web monitor integration
    archive_on_complete: bool = True  # Archive diagrams on session end
    max_sync_frequency: float = 0.5  # Maximum syncs per second


class TodoSyncService:
    """Service for synchronizing TODO updates to diagrams with debouncing."""

    def __init__(
        self,
        config: TodoSyncConfig | None = None,
        translator: TodoTranslator | None = None,
        execution_callback: Callable[[str], Any] | None = None,
    ):
        """
        Initialize the sync service.

        Args:
            config: Sync configuration
            translator: TODO to diagram translator
            execution_callback: Optional callback to execute generated diagrams
        """
        self.config = config or TodoSyncConfig()
        self.translator = translator or TodoTranslator()
        self.execution_callback = execution_callback

        # Sync state
        self._active_sessions: dict[str, SessionSyncState] = {}
        self._sync_tasks: dict[str, asyncio.Task] = {}
        self._last_sync_times: dict[str, datetime] = {}
        self._pending_snapshots: dict[str, TodoSnapshot] = {}

        # Ensure persistence directory exists
        self.config.persistence_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"[TodoSyncService] Initialized with mode={config.mode}, "
            f"debounce={config.debounce_seconds}s, path={config.persistence_path}"
        )

    async def register_session(self, session_id: str, trace_id: str | None = None) -> None:
        """
        Register a new session for TODO synchronization.

        Args:
            session_id: Claude Code session ID
            trace_id: Optional execution trace ID
        """
        if self.config.mode == TodoSyncMode.OFF:
            logger.debug(f"[TodoSyncService] Sync disabled, skipping session {session_id}")
            return

        if session_id in self._active_sessions:
            logger.warning(f"[TodoSyncService] Session {session_id} already registered")
            return

        # Create session state
        state = SessionSyncState(
            session_id=session_id,
            trace_id=trace_id,
            started_at=datetime.now(),
        )
        self._active_sessions[session_id] = state

        logger.info(f"[TodoSyncService] Registered session {session_id}")

        # Start auto-sync task if mode is AUTO or WATCH
        if self.config.mode in (TodoSyncMode.AUTO, TodoSyncMode.WATCH):
            await self._start_sync_task(session_id)

    async def unregister_session(self, session_id: str) -> None:
        """
        Unregister a session and perform cleanup.

        Args:
            session_id: Session to unregister
        """
        if session_id not in self._active_sessions:
            logger.warning(f"[TodoSyncService] Session {session_id} not registered")
            return

        # Stop any active sync task
        if session_id in self._sync_tasks:
            task = self._sync_tasks.pop(session_id)
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        # Archive final diagram if configured
        if self.config.archive_on_complete:
            await self._archive_session(session_id)

        # Clean up state
        self._active_sessions.pop(session_id, None)
        self._last_sync_times.pop(session_id, None)
        self._pending_snapshots.pop(session_id, None)

        logger.info(f"[TodoSyncService] Unregistered session {session_id}")

    async def handle_todo_update(self, session_id: str, snapshot: TodoSnapshot) -> None:
        """
        Handle a TODO update from TodoTaskCollector.

        This is the main entry point for TODO updates. The method will
        debounce rapid updates and trigger diagram generation.

        Args:
            session_id: Session that generated the update
            snapshot: The TODO snapshot
        """
        if self.config.mode == TodoSyncMode.OFF:
            return

        if session_id not in self._active_sessions:
            logger.warning(
                f"[TodoSyncService] Received update for unregistered session {session_id}"
            )
            return

        # Store pending snapshot
        self._pending_snapshots[session_id] = snapshot

        # Update session state
        state = self._active_sessions[session_id]
        state.last_update = datetime.now()
        state.update_count += 1

        logger.debug(
            f"[TodoSyncService] Received TODO update for session {session_id}, "
            f"update #{state.update_count}"
        )

        # Trigger sync based on mode
        if self.config.mode == TodoSyncMode.MANUAL:
            # In manual mode, just store the snapshot
            pass
        elif self.config.mode in (TodoSyncMode.AUTO, TodoSyncMode.WATCH):
            # Schedule debounced sync
            await self._schedule_debounced_sync(session_id)

    async def trigger_manual_sync(self, session_id: str) -> str | None:
        """
        Manually trigger a sync for a session.

        Args:
            session_id: Session to sync

        Returns:
            Path to generated diagram file, or None if no snapshot
        """
        if session_id not in self._pending_snapshots:
            logger.warning(f"[TodoSyncService] No pending snapshot for session {session_id}")
            return None

        snapshot = self._pending_snapshots.pop(session_id)
        return await self._perform_sync(session_id, snapshot)

    async def _start_sync_task(self, session_id: str) -> None:
        """Start an async task for automatic synchronization."""
        if session_id in self._sync_tasks:
            return  # Task already running

        async def sync_loop():
            """Main sync loop for a session."""
            try:
                while session_id in self._active_sessions:
                    # Wait for debounce period
                    await asyncio.sleep(self.config.debounce_seconds)

                    # Check if we have a pending snapshot
                    if session_id in self._pending_snapshots:
                        snapshot = self._pending_snapshots.pop(session_id)
                        await self._perform_sync(session_id, snapshot)

            except asyncio.CancelledError:
                logger.debug(f"[TodoSyncService] Sync task cancelled for {session_id}")
                raise
            except Exception as e:
                logger.error(
                    f"[TodoSyncService] Sync task error for {session_id}: {e}", exc_info=True
                )

        task = asyncio.create_task(sync_loop())
        self._sync_tasks[session_id] = task

    async def _schedule_debounced_sync(self, session_id: str) -> None:
        """Schedule a debounced sync operation."""
        # Check sync frequency limit
        now = datetime.now()
        last_sync = self._last_sync_times.get(session_id)

        if last_sync:
            time_since_last = (now - last_sync).total_seconds()
            min_interval = 1.0 / self.config.max_sync_frequency

            if time_since_last < min_interval:
                logger.debug(
                    f"[TodoSyncService] Throttling sync for {session_id}, "
                    f"last sync {time_since_last:.1f}s ago"
                )
                return

        # The sync task will pick up the pending snapshot
        # No need to do anything else here since the task is already running

    async def _perform_sync(self, session_id: str, snapshot: TodoSnapshot) -> str | None:
        """
        Perform the actual synchronization.

        Args:
            session_id: Session ID
            snapshot: TODO snapshot to sync

        Returns:
            Path to generated diagram file
        """
        try:
            logger.info(
                f"[TodoSyncService] Syncing {len(snapshot.todos)} TODOs for session {session_id}"
            )

            # Generate diagram
            diagram_id = f"todo_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            diagram = self.translator.translate(snapshot, diagram_id=diagram_id)

            # Save to file
            filename = f"{session_id}.light.yaml"
            output_path = self.config.persistence_path / filename
            saved_path = self.translator.save_to_file(diagram, output_path)

            # Update session state
            if session_id in self._active_sessions:
                state = self._active_sessions[session_id]
                state.last_sync = datetime.now()
                state.sync_count += 1
                state.last_diagram_path = str(saved_path)

            # Update last sync time
            self._last_sync_times[session_id] = datetime.now()

            logger.info(f"[TodoSyncService] Saved diagram to {saved_path}")

            # Execute diagram if configured
            if self.config.auto_execute and self.execution_callback:
                try:
                    await self.execution_callback(str(saved_path))
                    logger.info(f"[TodoSyncService] Executed diagram {saved_path}")
                except Exception as e:
                    logger.error(f"[TodoSyncService] Failed to execute diagram: {e}", exc_info=True)

            return str(saved_path)

        except Exception as e:
            logger.error(
                f"[TodoSyncService] Sync failed for session {session_id}: {e}", exc_info=True
            )
            return None

    async def _archive_session(self, session_id: str) -> None:
        """Archive a session's diagrams."""
        if session_id not in self._active_sessions:
            return

        state = self._active_sessions[session_id]
        if not state.last_diagram_path:
            return

        try:
            # Create archive directory
            archive_dir = self.config.persistence_path / "archive" / session_id
            archive_dir.mkdir(parents=True, exist_ok=True)

            # Move diagram to archive
            source = Path(state.last_diagram_path)
            if source.exists():
                dest = archive_dir / source.name
                source.rename(dest)
                logger.info(f"[TodoSyncService] Archived diagram to {dest}")

        except Exception as e:
            logger.error(
                f"[TodoSyncService] Failed to archive session {session_id}: {e}", exc_info=True
            )

    def get_session_state(self, session_id: str) -> dict[str, Any] | None:
        """Get the current state of a session."""
        if session_id not in self._active_sessions:
            return None

        state = self._active_sessions[session_id]
        return {
            "session_id": state.session_id,
            "trace_id": state.trace_id,
            "started_at": state.started_at.isoformat(),
            "last_update": state.last_update.isoformat() if state.last_update else None,
            "last_sync": state.last_sync.isoformat() if state.last_sync else None,
            "update_count": state.update_count,
            "sync_count": state.sync_count,
            "last_diagram_path": state.last_diagram_path,
        }

    def get_active_sessions(self) -> list[str]:
        """Get list of active session IDs."""
        return list(self._active_sessions.keys())


@dataclass
class SessionSyncState:
    """State for a synchronized session."""

    session_id: str
    trace_id: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    last_update: datetime | None = None
    last_sync: datetime | None = None
    update_count: int = 0
    sync_count: int = 0
    last_diagram_path: str | None = None
