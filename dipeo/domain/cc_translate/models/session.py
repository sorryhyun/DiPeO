"""Domain model for session data."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class SessionStatus(Enum):
    """Session status enumeration."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PROCESSING = "processing"


@dataclass
class SessionMetadata:
    """Metadata for a session."""

    session_id: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    event_count: int = 0
    tool_usage_count: dict[str, int] = field(default_factory=dict)
    file_operations: dict[str, list[str]] = field(default_factory=dict)
    status: SessionStatus = SessionStatus.ACTIVE
    tags: list[str] = field(default_factory=list)
    custom_data: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        """Validate metadata consistency."""
        errors = []

        if not self.session_id:
            errors.append("Session ID is required")

        if self.end_time and self.start_time and self.end_time < self.start_time:
            errors.append("End time cannot be before start time")

        if self.event_count < 0:
            errors.append("Event count cannot be negative")

        return errors

    def get_duration(self) -> float | None:
        """Get session duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class DomainSession:
    """Domain model representing a session."""

    session_id: str
    events: list = field(default_factory=list)  # List of DomainEvent
    metadata: SessionMetadata = field(default_factory=lambda: SessionMetadata(""))
    conversation_turns: list = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize metadata session_id if not set."""
        if not self.metadata.session_id:
            self.metadata.session_id = self.session_id

    def validate(self) -> list[str]:
        """Validate session data integrity."""
        errors = []

        # Validate metadata
        metadata_errors = self.metadata.validate()
        errors.extend(metadata_errors)

        # Validate session_id consistency
        if self.session_id != self.metadata.session_id:
            errors.append(f"Session ID mismatch: {self.session_id} != {self.metadata.session_id}")

        # Validate event count
        if len(self.events) != self.metadata.event_count:
            errors.append(
                f"Event count mismatch: {len(self.events)} != {self.metadata.event_count}"
            )

        return errors

    def add_event(self, event: Any) -> None:
        """Add an event to the session."""
        self.events.append(event)
        self.metadata.event_count = len(self.events)

    def remove_event(self, event_uuid: str) -> bool:
        """Remove an event by UUID."""
        initial_count = len(self.events)
        self.events = [e for e in self.events if getattr(e, "uuid", None) != event_uuid]
        removed = len(self.events) < initial_count
        if removed:
            self.metadata.event_count = len(self.events)
        return removed

    def get_event_by_uuid(self, event_uuid: str) -> Any | None:
        """Get an event by UUID."""
        for event in self.events:
            if getattr(event, "uuid", None) == event_uuid:
                return event
        return None

    def get_tool_events(self) -> list:
        """Get all events that use tools."""
        return [e for e in self.events if hasattr(e, "tool_name") and e.tool_name]

    def get_user_events(self) -> list:
        """Get all user events."""
        return [e for e in self.events if hasattr(e, "type") and e.type == "user"]

    def get_assistant_events(self) -> list:
        """Get all assistant events."""
        return [e for e in self.events if hasattr(e, "type") and e.type == "assistant"]

    def to_dict(self) -> dict:
        """Convert session to dictionary representation."""
        return {
            "session_id": self.session_id,
            "events": [e.to_dict() if hasattr(e, "to_dict") else str(e) for e in self.events],
            "metadata": {
                "session_id": self.metadata.session_id,
                "start_time": self.metadata.start_time.isoformat()
                if self.metadata.start_time
                else None,
                "end_time": self.metadata.end_time.isoformat() if self.metadata.end_time else None,
                "event_count": self.metadata.event_count,
                "tool_usage_count": self.metadata.tool_usage_count,
                "file_operations": self.metadata.file_operations,
                "status": self.metadata.status.value,
                "tags": self.metadata.tags,
                "custom_data": self.metadata.custom_data,
            },
            "conversation_turns": len(self.conversation_turns),
            "errors": self.errors,
            "warnings": self.warnings,
        }
