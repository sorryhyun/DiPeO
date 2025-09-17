"""TodoTaskCollector module for capturing TODO updates from Claude Code hooks."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_code_sdk.types import HookContext, HookJSONOutput

logger = logging.getLogger(__name__)


@dataclass
class TodoItem:
    """Represents a single TODO item from Claude Code."""

    content: str
    status: str  # "pending", "in_progress", "completed"
    active_form: str | None = None
    index: int | None = None


@dataclass
class TodoSnapshot:
    """Snapshot of TODO state at a specific point in time."""

    session_id: str
    trace_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    todos: list[TodoItem] = field(default_factory=list)
    doc_path: str | None = None
    hook_event_timestamp: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "todos": [
                {
                    "content": todo.content,
                    "status": todo.status,
                    "active_form": todo.active_form,
                    "index": todo.index,
                }
                for todo in self.todos
            ],
            "doc_path": self.doc_path,
            "hook_event_timestamp": (
                self.hook_event_timestamp.isoformat() if self.hook_event_timestamp else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TodoSnapshot":
        """Create snapshot from dictionary."""
        todos = [
            TodoItem(
                content=item["content"],
                status=item["status"],
                active_form=item.get("active_form"),
                index=item.get("index"),
            )
            for item in data.get("todos", [])
        ]

        return cls(
            session_id=data["session_id"],
            trace_id=data.get("trace_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            todos=todos,
            doc_path=data.get("doc_path"),
            hook_event_timestamp=(
                datetime.fromisoformat(data["hook_event_timestamp"])
                if data.get("hook_event_timestamp")
                else None
            ),
        )


class TodoTaskCollector:
    """Collects and processes TODO updates from Claude Code hooks."""

    def __init__(self, session_id: str, trace_id: str | None = None):
        """Initialize collector with session and trace identifiers."""
        self.session_id = session_id
        self.trace_id = trace_id
        self.current_snapshot: TodoSnapshot | None = None
        self._persistence_path = self._get_persistence_path()

        logger.info(
            f"[TodoTaskCollector] Initialized for session={session_id}, "
            f"trace={trace_id}, persistence={self._persistence_path}"
        )

    def _get_persistence_path(self) -> Path:
        """Get path for persisting snapshots."""
        import os

        root = os.getenv(
            "DIPEO_CLAUDE_WORKSPACES", os.path.join(os.getcwd(), ".dipeo", "workspaces")
        )

        # Use trace_id if available, otherwise session_id
        identifier = self.trace_id or self.session_id
        workspace_dir = Path(root) / f"exec_{identifier}"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        return workspace_dir / "todo_snapshot.json"

    async def handle_todo_write_hook(
        self, input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
    ) -> HookJSONOutput:
        """
        Handle PostToolUse hook for TodoWrite tool.

        This is the callback that will be registered as a hook matcher
        for PostToolUse events with TodoWrite as the matcher.
        """
        try:
            logger.debug(
                f"[TodoTaskCollector] Processing TodoWrite hook: "
                f"tool_use_id={tool_use_id}, input_preview={str(input_data)[:200]}"
            )

            # Extract TODO data from the hook input
            # Based on TodoWrite tool structure, we expect:
            # - input_data["todos"]: list of todo items
            # Each todo item has: content, status, activeForm

            tool_input = input_data.get("input", {})
            todos_data = tool_input.get("todos", [])

            if not todos_data:
                logger.warning("[TodoTaskCollector] No todos found in hook input")
                return {"decision": None}

            # Create TodoItems from the data
            todos = []
            for i, todo_data in enumerate(todos_data):
                todo = TodoItem(
                    content=todo_data.get("content", ""),
                    status=todo_data.get("status", "pending"),
                    active_form=todo_data.get("activeForm"),
                    index=i,
                )
                todos.append(todo)

            # Create or update snapshot
            self.current_snapshot = TodoSnapshot(
                session_id=self.session_id,
                trace_id=self.trace_id,
                timestamp=datetime.now(),
                todos=todos,
                doc_path=input_data.get("doc_path"),
                hook_event_timestamp=datetime.now(),
            )

            # Persist snapshot
            await self.persist_snapshot()

            logger.info(
                f"[TodoTaskCollector] Captured {len(todos)} TODO items: "
                f"{', '.join(t.status for t in todos[:3])}..."
            )

            # Return hook output (don't block the action)
            return {
                "decision": None,  # Don't block
                "systemMessage": f"TODO snapshot captured: {len(todos)} items",
            }

        except Exception as e:
            logger.error(f"[TodoTaskCollector] Error processing hook: {e}", exc_info=True)
            # Don't block on error, just log it
            return {
                "decision": None,
                "systemMessage": f"TODO collection error (non-blocking): {e!s}",
            }

    async def persist_snapshot(self) -> None:
        """Persist current snapshot to JSON file."""
        if not self.current_snapshot:
            logger.warning("[TodoTaskCollector] No snapshot to persist")
            return

        try:
            # Write snapshot to JSON file
            with open(self._persistence_path, "w") as f:
                json.dump(self.current_snapshot.to_dict(), f, indent=2)

            logger.debug(f"[TodoTaskCollector] Persisted snapshot to {self._persistence_path}")

        except Exception as e:
            logger.error(f"[TodoTaskCollector] Failed to persist snapshot: {e}", exc_info=True)

    async def load_snapshot(self) -> TodoSnapshot | None:
        """Load existing snapshot from persistence."""
        if not self._persistence_path.exists():
            logger.debug("[TodoTaskCollector] No existing snapshot found")
            return None

        try:
            with open(self._persistence_path) as f:
                data = json.load(f)

            snapshot = TodoSnapshot.from_dict(data)
            self.current_snapshot = snapshot

            logger.debug(f"[TodoTaskCollector] Loaded snapshot with {len(snapshot.todos)} todos")

            return snapshot

        except Exception as e:
            logger.error(f"[TodoTaskCollector] Failed to load snapshot: {e}", exc_info=True)
            return None

    def get_current_snapshot(self) -> TodoSnapshot | None:
        """Get current TODO snapshot."""
        return self.current_snapshot

    def create_hook_config(self) -> dict[str, list[dict]]:
        """
        Create hook configuration dict for UnifiedClaudeCodeClient.

        Returns a hooks_config dict that can be passed to async_chat/stream.
        """
        return {"PostToolUse": [{"matcher": "TodoWrite", "hooks": [self.handle_todo_write_hook]}]}
