"""Claude Code session parser for converting JSONL session files to structured data."""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class SessionEvent:
    """Represents a single event in a Claude Code session."""

    type: str  # user/assistant/summary
    uuid: str
    message: dict[str, Any]
    timestamp: datetime
    parent_uuid: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[dict[str, Any]] = None
    tool_results: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "SessionEvent":
        """Create SessionEvent from JSON data."""
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

        # Extract tool usage from assistant messages
        tool_name = None
        tool_input = None
        tool_results = []

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

        return cls(
            type=data["type"],
            uuid=data.get("uuid", ""),
            message=data.get("message", {}),
            timestamp=timestamp,
            parent_uuid=data.get("parentUuid"),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_results=tool_results,
        )


@dataclass
class ConversationTurn:
    """Represents a user-assistant interaction pair."""

    user_event: SessionEvent
    assistant_event: Optional[SessionEvent] = None
    tool_events: list[SessionEvent] = field(default_factory=list)


@dataclass
class SessionMetadata:
    """Metadata about a Claude Code session."""

    session_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_count: int = 0
    tool_usage_count: dict[str, int] = field(default_factory=dict)
    file_operations: dict[str, list[str]] = field(default_factory=dict)


class ClaudeCodeSession:
    """Parser and analyzer for Claude Code session JSONL files."""

    def __init__(self, session_id: str):
        """Initialize session with given ID."""
        self.session_id = session_id
        self.events: list[SessionEvent] = []
        self.metadata = SessionMetadata(session_id=session_id)

    def load_from_file(self, file_path: Path) -> None:
        """Load session events from a JSONL file."""
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

        self._update_metadata()

    def parse_events(self) -> list[SessionEvent]:
        """Parse and return all session events."""
        return self.events

    def extract_tool_usage(self) -> dict[str, int]:
        """Extract and count tool usage from events."""
        tool_counts = defaultdict(int)

        for event in self.events:
            if event.tool_name:
                tool_counts[event.tool_name] += 1

        return dict(tool_counts)

    def get_conversation_flow(self) -> list[ConversationTurn]:
        """Extract conversation flow as user-assistant pairs."""
        turns = []
        current_turn = None

        for event in self.events:
            if event.type == "user":
                # Start a new turn
                if current_turn:
                    turns.append(current_turn)
                current_turn = ConversationTurn(user_event=event)

            elif event.type == "assistant" and current_turn:
                # Add assistant response to current turn
                if not current_turn.assistant_event:
                    current_turn.assistant_event = event

                # Collect tool events
                if event.tool_name:
                    current_turn.tool_events.append(event)

        # Add the last turn if exists
        if current_turn:
            turns.append(current_turn)

        return turns

    def get_file_operations(self) -> dict[str, list[str]]:
        """Extract all file operations (Read, Write, Edit) from the session."""
        operations = defaultdict(list)

        for event in self.events:
            if event.tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
                if event.tool_input and "file_path" in event.tool_input:
                    file_path = event.tool_input["file_path"]
                    operations[event.tool_name].append(file_path)

        return dict(operations)

    def get_bash_commands(self) -> list[str]:
        """Extract all bash commands executed in the session."""
        commands = []

        for event in self.events:
            if event.tool_name == "Bash" and event.tool_input:
                if "command" in event.tool_input:
                    commands.append(event.tool_input["command"])

        return commands

    def _update_metadata(self) -> None:
        """Update session metadata based on parsed events."""
        if not self.events:
            return

        self.metadata.start_time = self.events[0].timestamp
        self.metadata.end_time = self.events[-1].timestamp
        self.metadata.event_count = len(self.events)
        self.metadata.tool_usage_count = self.extract_tool_usage()
        self.metadata.file_operations = self.get_file_operations()

    def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics about the session."""
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
    """Find Claude Code session JSONL files in the given directory."""
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


def parse_session_file(file_path: Path) -> ClaudeCodeSession:
    """Convenience function to parse a session file."""
    # Extract session ID from filename (assuming format: session-{id}.jsonl)
    session_id = file_path.stem.replace("session-", "")

    session = ClaudeCodeSession(session_id)
    session.load_from_file(file_path)

    return session
