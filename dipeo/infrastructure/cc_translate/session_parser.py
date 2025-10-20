"""Claude Code session parser for converting JSONL session files to structured data."""

import contextlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class SessionEvent:
    type: str  # user/assistant/summary
    uuid: str
    message: dict[str, Any]
    timestamp: datetime
    parent_uuid: str | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    # New fields for richer event context
    role: str | None = None  # Role from message (user/assistant/system)
    user_type: str | None = None  # Type of user (external/internal)
    is_meta: bool = False  # Whether this is a meta/system event
    tool_use_result: dict[str, Any] | None = None  # Full tool result payload

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "SessionEvent":
        timestamp = datetime.now()
        if "timestamp" in data:
            with contextlib.suppress(ValueError, AttributeError):
                timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

        # Extract tool usage from assistant messages
        tool_name = None
        tool_input = None
        tool_results = []
        tool_use_result = None

        if data["type"] == "assistant" and "message" in data:
            message = data["message"]
            if "content" in message and isinstance(message["content"], list):
                for content_item in message["content"]:
                    if isinstance(content_item, dict):
                        if content_item.get("type") == "tool_use":
                            tool_name = content_item.get("name")
                            tool_input = content_item.get("input", {})
                        elif content_item.get("type") == "tool_result":
                            tool_results.append(content_item)

        # Extract tool use result payload if present
        if "toolUseResult" in data:
            tool_use_result = data["toolUseResult"]

        # Extract role from message if present
        role = None
        if "message" in data and isinstance(data["message"], dict):
            role = data["message"].get("role")

        return cls(
            type=data["type"],
            uuid=data.get("uuid", ""),
            message=data.get("message", {}),
            timestamp=timestamp,
            parent_uuid=data.get("parentUuid"),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_results=tool_results,
            # New fields
            role=role,
            user_type=data.get("userType"),
            is_meta=data.get("isMeta", False),
            tool_use_result=tool_use_result,
        )


@dataclass
class ConversationTurn:
    user_event: SessionEvent
    assistant_event: SessionEvent | None = None
    tool_events: list[SessionEvent] = field(default_factory=list)
    meta_events: list[SessionEvent] = field(default_factory=list)  # System/meta events


@dataclass
class SessionMetadata:
    session_id: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    event_count: int = 0
    tool_usage_count: dict[str, int] = field(default_factory=dict)
    file_operations: dict[str, list[str]] = field(default_factory=dict)


class ClaudeCodeSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: list[SessionEvent] = []
        self.metadata = SessionMetadata(session_id=session_id)

    def load_from_file(self, file_path: Path) -> None:
        if not file_path.exists():
            raise FileNotFoundError(f"Session file not found: {file_path}")

        self.events.clear()

        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)
                    event = SessionEvent.from_json(data)
                    self.events.append(event)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}")
                except Exception as e:
                    print(f"Warning: Error processing line {line_num}: {e}")

        self._associate_tool_results()
        self._update_metadata()

    def _associate_tool_results(self) -> None:
        """Associate tool result payloads with their originating tool events.

        Claude Code sessions emit tool results as separate user events that
        reference the originating assistant/tool event via ``parentUuid``.
        This method links those payloads back to the tool event so downstream
        translators can access rich ``tool_use_result`` data (original file
        contents, structured patches, etc.).

        Priority order for result payloads:
        1. Structured dict with patch data (rich diff)
        2. Structured dict without patch (write/read result)
        3. List of structured payloads (prefer last)
        4. Error strings or primitive values (fallback)
        """

        if not self.events:
            return

        events_by_uuid = {event.uuid: event for event in self.events if event.uuid}

        for event in self.events:
            if not event.tool_use_result or not event.parent_uuid:
                continue

            parent_event = events_by_uuid.get(event.parent_uuid)
            if not parent_event or not parent_event.tool_name:
                continue

            result_payload = event.tool_use_result

            # Skip if parent already has a rich payload (don't overwrite with worse data)
            if parent_event.tool_use_result and isinstance(parent_event.tool_use_result, dict):
                existing = parent_event.tool_use_result
                # Check if existing payload has rich diff data
                has_rich_data = any(
                    key in existing
                    for key in [
                        "structuredPatch",
                        "patch",
                        "diff",
                        "originalFile",
                        "originalFileContents",
                    ]
                )
                if has_rich_data:
                    continue  # Keep existing rich payload

            # Prefer structured payloads when multiple results are emitted.
            if isinstance(result_payload, dict):
                # Always prefer dict payloads
                parent_event.tool_use_result = result_payload
            elif isinstance(result_payload, list):
                # Use the last structured payload if available, preferring rich diffs
                best_payload = None
                for item in reversed(result_payload):
                    if isinstance(item, dict):
                        # Check if this is a rich diff payload
                        has_patch = any(key in item for key in ["structuredPatch", "patch", "diff"])
                        if has_patch:
                            # Found a rich diff, use it immediately
                            parent_event.tool_use_result = item
                            best_payload = None
                            break
                        elif best_payload is None:
                            # Remember first dict we find as fallback
                            best_payload = item

                # Use best dict found, or list if no dicts
                if best_payload is not None:
                    parent_event.tool_use_result = best_payload
                elif parent_event.tool_use_result is None:
                    parent_event.tool_use_result = result_payload
            else:
                # Only attach plain strings if we do not already have
                # structured information (avoids clobbering rich payloads).
                if parent_event.tool_use_result is None:
                    parent_event.tool_use_result = result_payload

    def parse_events(self) -> list[SessionEvent]:
        return self.events

    def extract_tool_usage(self) -> dict[str, int]:
        tool_counts = defaultdict(int)

        for event in self.events:
            if event.tool_name:
                tool_counts[event.tool_name] += 1

        return dict(tool_counts)

    def get_conversation_flow(self) -> list[ConversationTurn]:
        turns = []
        current_turn = None
        pending_meta_events = []  # Collect meta events before each turn

        for event in self.events:
            # Collect meta/system events
            if event.is_meta:
                pending_meta_events.append(event)
                continue

            if event.type == "user":
                # Skip non-meaningful user events (command wrappers, empty stdout)
                if self._is_command_wrapper_event(event):
                    continue

                # Start a new turn
                if current_turn:
                    turns.append(current_turn)
                current_turn = ConversationTurn(user_event=event)

                # Attach any pending meta events to this turn
                if pending_meta_events:
                    current_turn.meta_events.extend(pending_meta_events)
                    pending_meta_events = []

            elif event.type == "assistant" and current_turn:
                # Add assistant response to current turn
                if not current_turn.assistant_event:
                    current_turn.assistant_event = event

                # Collect tool events
                if event.tool_name:
                    current_turn.tool_events.append(event)

        # Add the last turn if exists
        if current_turn:
            # Attach any remaining meta events
            if pending_meta_events:
                current_turn.meta_events.extend(pending_meta_events)
            turns.append(current_turn)

        return turns

    def get_file_operations(self) -> dict[str, list[str]]:
        operations = defaultdict(list)

        for event in self.events:
            if event.tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
                if event.tool_input and "file_path" in event.tool_input:
                    file_path = event.tool_input["file_path"]
                    operations[event.tool_name].append(file_path)

        return dict(operations)

    def get_bash_commands(self) -> list[str]:
        commands = []

        for event in self.events:
            if event.tool_name == "Bash" and event.tool_input:
                if "command" in event.tool_input:
                    commands.append(event.tool_input["command"])

        return commands

    def _is_command_wrapper_event(self, event: SessionEvent) -> bool:
        if event.type != "user":
            return False

        message = event.message
        if not message or "content" not in message:
            return False

        content = message["content"]

        # Check for command wrapper pattern (e.g., /clear commands)
        if isinstance(content, str):
            # Skip command wrappers
            if content.startswith("<command-name>") and "</command-name>" in content:
                return True
            # Skip empty stdout
            if content.strip() == "<local-command-stdout></local-command-stdout>":
                return True

        return False

    def _update_metadata(self) -> None:
        if not self.events:
            return

        self.metadata.start_time = self.events[0].timestamp
        self.metadata.end_time = self.events[-1].timestamp
        self.metadata.event_count = len(self.events)
        self.metadata.tool_usage_count = self.extract_tool_usage()
        self.metadata.file_operations = self.get_file_operations()

    def get_summary_stats(self) -> dict[str, Any]:
        stats = {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "user_messages": sum(1 for e in self.events if e.type == "user"),
            "assistant_messages": sum(1 for e in self.events if e.type == "assistant"),
            "tool_usage": self.metadata.tool_usage_count,
            "unique_files_accessed": len(
                set(
                    file_path
                    for files in self.metadata.file_operations.values()
                    for file_path in files
                )
            ),
            "bash_commands_executed": len(self.get_bash_commands()),
        }

        if self.metadata.start_time and self.metadata.end_time:
            duration = self.metadata.end_time - self.metadata.start_time
            stats["duration_seconds"] = duration.total_seconds()
            stats["duration_human"] = str(duration)

        return stats


def find_session_files(base_dir: Path, limit: int = 50) -> list[Path]:
    session_files = []

    if not base_dir.exists():
        return session_files

    # Look for JSONL files
    for jsonl_file in sorted(
        base_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    ):
        session_files.append(jsonl_file)
        if len(session_files) >= limit:
            break

    return session_files


def extract_session_timestamp(file_path: Path) -> datetime | None:
    if not file_path.exists():
        return None

    try:
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if "timestamp" in data:
                        timestamp_str = data["timestamp"]
                        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return None


def format_timestamp_for_directory(timestamp: datetime) -> str:
    return timestamp.strftime("%Y-%m-%d_%H-%M-%S")


def parse_session_file(file_path: Path) -> ClaudeCodeSession:
    session_id = file_path.stem.replace("session-", "")

    session = ClaudeCodeSession(session_id)
    session.load_from_file(file_path)

    return session
