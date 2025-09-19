"""
GraphQL resolvers for TODO sync operations.
"""

import json
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Optional

import strawberry
from strawberry.types import Info

from dipeo.application.todo_sync.sync_service import TodoSyncMode, TodoSyncService
from dipeo.domain.diagram.services.todo_translator import TodoTranslator
from dipeo.infrastructure.llm.providers.claude_code.todo_collector import (
    TodoSnapshot,
    TodoTaskCollector,
)


@strawberry.type
class TodoSyncStatus:
    """Status of TODO sync for a session."""

    session_id: str
    is_active: bool
    sync_count: int
    last_sync: Optional[datetime]
    diagram_path: Optional[str]


@strawberry.type
class TodoSyncActiveSession:
    """Active TODO sync session details."""

    session_id: str
    started_at: datetime
    last_update: Optional[datetime]
    update_count: int


@strawberry.type
class TodoSyncStatusResult:
    """Complete TODO sync status with active sessions."""

    session_id: Optional[str]
    is_active: bool
    sync_count: int
    last_sync: Optional[datetime]
    diagram_path: Optional[str]
    active_sessions: list[TodoSyncActiveSession]


@strawberry.type
class TodoDiagramMetadata:
    """Metadata for a TODO diagram."""

    trace_id: Optional[str]
    hook_timestamp: Optional[datetime]
    doc_path: Optional[str]


@strawberry.type
class TodoDiagram:
    """A diagram generated from TODO items."""

    id: str
    name: str
    session_id: str
    originating_document: Optional[str]
    created_at: datetime
    updated_at: datetime
    todo_count: int
    completed_count: int
    in_progress_count: int
    pending_count: int
    last_sync: datetime
    is_active: bool
    diagram_path: str
    metadata: Optional[TodoDiagramMetadata]


@strawberry.type
class TodoItem:
    """Individual TODO item."""

    content: str
    status: str
    active_form: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@strawberry.type
class TodoDiagramWithItems:
    """TODO diagram with its items."""

    id: str
    name: str
    session_id: str
    originating_document: Optional[str]
    created_at: datetime
    updated_at: datetime
    todo_count: int
    completed_count: int
    in_progress_count: int
    pending_count: int
    last_sync: datetime
    is_active: bool
    diagram_path: str
    metadata: Optional[TodoDiagramMetadata]
    todos: list[TodoItem]


@strawberry.type
class TodoSyncResult:
    """Result of a TODO sync operation."""

    success: bool
    message: str
    error: Optional[str]
    data: Optional[strawberry.scalars.JSON]
    sync_status: Optional[TodoSyncStatus]


@strawberry.type
class TodoSyncConfig:
    """TODO sync configuration."""

    mode: str
    output_dir: str
    auto_execute: bool
    monitor_enabled: bool
    debounce_seconds: float


@strawberry.type
class TodoSyncConfigResult:
    """Result of TODO sync configuration."""

    success: bool
    message: str
    error: Optional[str]
    data: Optional[strawberry.scalars.JSON]
    config: Optional[TodoSyncConfig]


@strawberry.type
class TodoSyncTriggerResult:
    """Result of manually triggering TODO sync."""

    success: bool
    message: str
    error: Optional[str]
    data: Optional[strawberry.scalars.JSON]
    diagram_path: Optional[str]


@strawberry.type
class TodoSnapshotItems:
    """TODO snapshot items."""

    content: str
    status: str
    active_form: str


@strawberry.type
class TodoSnapshotData:
    """TODO snapshot data."""

    items: list[TodoSnapshotItems]
    timestamp: datetime
    session_id: str


@strawberry.type
class TodoUpdateEvent:
    """Event for TODO updates subscription."""

    event_type: str  # 'sync', 'update', 'complete'
    session_id: str
    timestamp: datetime
    diagram: Optional[TodoDiagram]
    todo_snapshot: Optional[TodoSnapshotData]


class TodoSyncResolvers:
    """GraphQL resolvers for TODO sync operations."""

    def __init__(self):
        self.sync_service = TodoSyncService()
        self.translator = TodoTranslator()

    async def toggle_todo_sync(
        self, info: Info, session_id: str, enabled: bool, trace_id: Optional[str] = None
    ) -> TodoSyncResult:
        """Toggle TODO sync for a session."""
        try:
            if enabled:
                # Enable sync for session
                self.sync_service.register_session(session_id, trace_id=trace_id)
                message = f"TODO sync enabled for session {session_id}"
            else:
                # Disable sync for session
                self.sync_service.unregister_session(session_id)
                message = f"TODO sync disabled for session {session_id}"

            # Get current status
            session_info = self.sync_service.get_session_state(session_id)

            return TodoSyncResult(
                success=True,
                message=message,
                error=None,
                data=None,
                sync_status=TodoSyncStatus(
                    session_id=session_id,
                    is_active=session_info is not None,
                    sync_count=session_info.get("sync_count", 0) if session_info else 0,
                    last_sync=session_info.get("last_sync") if session_info else None,
                    diagram_path=session_info.get("diagram_path") if session_info else None,
                )
                if session_info
                else None,
            )
        except Exception as e:
            return TodoSyncResult(
                success=False,
                message="Failed to toggle TODO sync",
                error=str(e),
                data=None,
                sync_status=None,
            )

    async def configure_todo_sync(
        self,
        info: Info,
        mode: str,
        output_dir: Optional[str] = None,
        auto_execute: Optional[bool] = None,
        monitor_enabled: Optional[bool] = None,
        debounce_seconds: Optional[float] = None,
    ) -> TodoSyncConfigResult:
        """Configure TODO sync settings."""
        try:
            # Update configuration
            if mode:
                self.sync_service.sync_mode = TodoSyncMode[mode.upper()]
            if output_dir:
                self.sync_service.output_dir = Path(output_dir)
            if auto_execute is not None:
                self.sync_service.auto_execute = auto_execute
            if monitor_enabled is not None:
                self.sync_service.monitor_enabled = monitor_enabled
            if debounce_seconds is not None:
                self.sync_service.debounce_seconds = debounce_seconds

            return TodoSyncConfigResult(
                success=True,
                message="TODO sync configuration updated",
                error=None,
                data=None,
                config=TodoSyncConfig(
                    mode=self.sync_service.sync_mode.value,
                    output_dir=str(self.sync_service.output_dir),
                    auto_execute=self.sync_service.auto_execute,
                    monitor_enabled=self.sync_service.monitor_enabled,
                    debounce_seconds=self.sync_service.debounce_seconds,
                ),
            )
        except Exception as e:
            return TodoSyncConfigResult(
                success=False,
                message="Failed to configure TODO sync",
                error=str(e),
                data=None,
                config=None,
            )

    async def trigger_todo_sync(self, info: Info, session_id: str) -> TodoSyncTriggerResult:
        """Manually trigger TODO sync for a session."""
        try:
            # Trigger sync
            diagram_path = await self.sync_service.sync_session(session_id)

            return TodoSyncTriggerResult(
                success=True,
                message=f"TODO sync triggered for session {session_id}",
                error=None,
                data=None,
                diagram_path=str(diagram_path) if diagram_path else None,
            )
        except Exception as e:
            return TodoSyncTriggerResult(
                success=False,
                message="Failed to trigger TODO sync",
                error=str(e),
                data=None,
                diagram_path=None,
            )

    async def todo_sync_status(
        self, info: Info, session_id: Optional[str] = None
    ) -> TodoSyncStatusResult:
        """Get TODO sync status."""
        try:
            if session_id:
                # Get status for specific session
                session_info = self.sync_service.get_session_state(session_id)
                is_active = session_info is not None

                return TodoSyncStatusResult(
                    session_id=session_id,
                    is_active=is_active,
                    sync_count=session_info.get("sync_count", 0) if session_info else 0,
                    last_sync=session_info.get("last_sync") if session_info else None,
                    diagram_path=session_info.get("diagram_path") if session_info else None,
                    active_sessions=[],
                )
            else:
                # Get all active sessions
                active_sessions = []
                for sid, sinfo in self.sync_service._active_sessions.items():
                    active_sessions.append(
                        TodoSyncActiveSession(
                            session_id=sid,
                            started_at=sinfo.get("started_at", datetime.now()),
                            last_update=sinfo.get("last_sync"),
                            update_count=sinfo.get("sync_count", 0),
                        )
                    )

                return TodoSyncStatusResult(
                    session_id=None,
                    is_active=len(active_sessions) > 0,
                    sync_count=0,
                    last_sync=None,
                    diagram_path=None,
                    active_sessions=active_sessions,
                )
        except Exception as e:
            return TodoSyncStatusResult(
                session_id=session_id,
                is_active=False,
                sync_count=0,
                last_sync=None,
                diagram_path=None,
                active_sessions=[],
            )

    async def todo_diagrams(
        self,
        info: Info,
        session_id: Optional[str] = None,
        originating_document: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[TodoDiagram]:
        """List TODO-backed diagrams with filtering."""
        try:
            diagrams = []
            base_dir = Path("/home/soryhyun/DiPeO/projects/dipeo_cc")

            # Get diagram files
            if base_dir.exists():
                for diagram_file in base_dir.glob("*.light.yaml"):
                    # Parse diagram metadata
                    with open(diagram_file) as f:
                        content = f.read()
                        # Extract metadata (simple parsing for now)
                        # In production, properly parse YAML

                        # Apply filters
                        if session_id and session_id not in str(diagram_file):
                            continue

                        # Create diagram object
                        diagrams.append(
                            TodoDiagram(
                                id=diagram_file.stem,
                                name=diagram_file.stem,
                                session_id=session_id or diagram_file.stem.split("-")[0]
                                if "-" in diagram_file.stem
                                else diagram_file.stem,
                                originating_document=originating_document,
                                created_at=datetime.fromtimestamp(diagram_file.stat().st_ctime),
                                updated_at=datetime.fromtimestamp(diagram_file.stat().st_mtime),
                                todo_count=0,  # Would need to parse file
                                completed_count=0,
                                in_progress_count=0,
                                pending_count=0,
                                last_sync=datetime.fromtimestamp(diagram_file.stat().st_mtime),
                                is_active=is_active if is_active is not None else False,
                                diagram_path=str(diagram_file),
                                metadata=None,
                            )
                        )

            # Apply pagination
            if offset:
                diagrams = diagrams[offset:]
            if limit:
                diagrams = diagrams[:limit]

            return diagrams
        except Exception as e:
            return []

    async def todo_diagram(self, info: Info, id: str) -> Optional[TodoDiagramWithItems]:
        """Get a single TODO diagram with its items."""
        try:
            diagram_path = Path(f"/home/soryhyun/DiPeO/projects/dipeo_cc/{id}.light.yaml")

            if not diagram_path.exists():
                return None

            # Load and parse diagram
            # In production, properly parse YAML and extract TODO items

            return TodoDiagramWithItems(
                id=id,
                name=id,
                session_id=id.split("-")[0] if "-" in id else id,
                originating_document=None,
                created_at=datetime.fromtimestamp(diagram_path.stat().st_ctime),
                updated_at=datetime.fromtimestamp(diagram_path.stat().st_mtime),
                todo_count=0,
                completed_count=0,
                in_progress_count=0,
                pending_count=0,
                last_sync=datetime.fromtimestamp(diagram_path.stat().st_mtime),
                is_active=False,
                diagram_path=str(diagram_path),
                metadata=None,
                todos=[],
            )
        except Exception as e:
            return None

    async def todo_updates(self, info: Info, session_id: str) -> AsyncIterator[TodoUpdateEvent]:
        """Subscribe to TODO updates for a session."""
        # This would need integration with the sync service's event system
        # For now, yield a placeholder
        import asyncio

        while True:
            await asyncio.sleep(5)

            # Check for updates
            session_info = self.sync_service.get_session_state(session_id)
            if session_info:
                yield TodoUpdateEvent(
                    event_type="sync",
                    session_id=session_id,
                    timestamp=datetime.now(),
                    diagram=None,
                    todo_snapshot=None,
                )


# Create singleton instance
todo_sync_resolvers = TodoSyncResolvers()


# Export resolver functions matching operation naming convention
async def get_todo_sync_status(registry, **kwargs):
    """Query resolver for GetTodoSyncStatus."""
    return await todo_sync_resolvers.todo_sync_status(None, **kwargs)


async def list_todo_diagrams(registry, **kwargs):
    """Query resolver for ListTodoDiagrams."""
    return await todo_sync_resolvers.todo_diagrams(None, **kwargs)


async def get_todo_diagram(registry, **kwargs):
    """Query resolver for GetTodoDiagram."""
    return await todo_sync_resolvers.todo_diagram(None, **kwargs)


async def toggle_todo_sync(registry, **kwargs):
    """Mutation resolver for ToggleTodoSync."""
    # Extract input from kwargs
    input_data = kwargs.get("input", {})
    return await todo_sync_resolvers.toggle_todo_sync(
        None,
        session_id=input_data.get("session_id"),
        enabled=input_data.get("enabled"),
        trace_id=input_data.get("trace_id"),
    )


async def configure_todo_sync(registry, **kwargs):
    """Mutation resolver for ConfigureTodoSync."""
    # Extract input from kwargs
    input_data = kwargs.get("input", {})
    return await todo_sync_resolvers.configure_todo_sync(
        None,
        mode=input_data.get("mode"),
        output_dir=input_data.get("output_dir"),
        auto_execute=input_data.get("auto_execute"),
        monitor_enabled=input_data.get("monitor_enabled"),
        debounce_seconds=input_data.get("debounce_seconds"),
    )


async def trigger_todo_sync(registry, **kwargs):
    """Mutation resolver for TriggerTodoSync."""
    return await todo_sync_resolvers.trigger_todo_sync(None, session_id=kwargs.get("session_id"))


async def subscribe_todo_updates(registry, **kwargs):
    """Subscription resolver for SubscribeTodoUpdates."""
    async for event in todo_sync_resolvers.todo_updates(None, **kwargs):
        yield event
