"""Domain model for event data."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EventType(Enum):
    """Event type enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SUMMARY = "summary"
    SYSTEM = "system"
    META = "meta"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class EventRole(Enum):
    """Event role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ToolInfo:
    """Information about tool usage in an event."""

    name: str
    input_params: dict[str, Any] = field(default_factory=dict)
    results: list[dict[str, Any]] = field(default_factory=list)
    status: str = "pending"  # pending, success, failed
    error_message: str | None = None
    execution_time_ms: int | None = None

    def validate(self) -> list[str]:
        """Validate tool information."""
        errors = []

        if not self.name:
            errors.append("Tool name is required")

        if self.status not in ["pending", "success", "failed"]:
            errors.append(f"Invalid tool status: {self.status}")

        if self.status == "failed" and not self.error_message:
            errors.append("Error message required for failed tool execution")

        return errors


@dataclass
class EventContent:
    """Content of an event."""

    text: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_content(self) -> bool:
        """Check if event has any content."""
        return bool(self.text or self.data or self.attachments)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "data": self.data,
            "attachments": self.attachments,
            "metadata": self.metadata,
        }


@dataclass
class DomainEvent:
    """Domain model representing an event."""

    uuid: str
    type: EventType
    timestamp: datetime
    content: EventContent = field(default_factory=EventContent)
    parent_uuid: str | None = None
    role: EventRole | None = None
    tool_info: ToolInfo | None = None
    is_meta: bool = False
    user_type: str | None = None  # external/internal
    tags: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        """Validate event data integrity."""
        errors = []

        # Required fields
        if not self.uuid:
            errors.append("Event UUID is required")

        # Validate timestamp
        if not isinstance(self.timestamp, datetime):
            errors.append("Timestamp must be a datetime object")

        # Validate tool info if present
        if self.tool_info:
            tool_errors = self.tool_info.validate()
            errors.extend([f"Tool: {e}" for e in tool_errors])

        # Check consistency between type and tool_info
        if self.type in [EventType.TOOL_USE, EventType.TOOL_RESULT]:
            if not self.tool_info:
                errors.append(f"Tool info required for event type {self.type.value}")

        # Validate role consistency
        if self.role and self.type == EventType.USER and self.role != EventRole.USER:
            errors.append("User event must have user role")

        if self.role and self.type == EventType.ASSISTANT and self.role != EventRole.ASSISTANT:
            errors.append("Assistant event must have assistant role")

        return errors

    def has_tool_use(self) -> bool:
        """Check if event contains tool usage."""
        return self.tool_info is not None

    def get_tool_name(self) -> str | None:
        """Get tool name if applicable."""
        return self.tool_info.name if self.tool_info else None

    def get_tool_results(self) -> list[dict[str, Any]]:
        """Get tool results if applicable."""
        return self.tool_info.results if self.tool_info else []

    def is_user_event(self) -> bool:
        """Check if this is a user event."""
        return self.type == EventType.USER

    def is_assistant_event(self) -> bool:
        """Check if this is an assistant event."""
        return self.type == EventType.ASSISTANT

    def is_system_event(self) -> bool:
        """Check if this is a system/meta event."""
        return self.type == EventType.SYSTEM or self.is_meta

    def to_dict(self) -> dict:
        """Convert event to dictionary representation."""
        result = {
            "uuid": self.uuid,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content.to_dict(),
            "parent_uuid": self.parent_uuid,
            "role": self.role.value if self.role else None,
            "is_meta": self.is_meta,
            "user_type": self.user_type,
            "tags": self.tags,
            "context": self.context,
        }

        if self.tool_info:
            result["tool_info"] = {
                "name": self.tool_info.name,
                "input_params": self.tool_info.input_params,
                "results": self.tool_info.results,
                "status": self.tool_info.status,
                "error_message": self.tool_info.error_message,
                "execution_time_ms": self.tool_info.execution_time_ms,
            }

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "DomainEvent":
        """Create DomainEvent from dictionary."""
        # Parse timestamp
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # Parse event type
        event_type = data.get("type", "user")
        if isinstance(event_type, str):
            event_type = EventType(event_type)

        # Parse role
        role = data.get("role")
        if role and isinstance(role, str):
            role = EventRole(role)

        # Parse content
        content_data = data.get("content", {})
        if isinstance(content_data, dict):
            content = EventContent(**content_data)
        else:
            content = EventContent(text=str(content_data))

        # Parse tool info
        tool_info = None
        if "tool_info" in data:
            tool_data = data["tool_info"]
            tool_info = ToolInfo(
                name=tool_data.get("name", ""),
                input_params=tool_data.get("input_params", {}),
                results=tool_data.get("results", []),
                status=tool_data.get("status", "pending"),
                error_message=tool_data.get("error_message"),
                execution_time_ms=tool_data.get("execution_time_ms"),
            )

        return cls(
            uuid=data.get("uuid", ""),
            type=event_type,
            timestamp=timestamp,
            content=content,
            parent_uuid=data.get("parent_uuid"),
            role=role,
            tool_info=tool_info,
            is_meta=data.get("is_meta", False),
            user_type=data.get("user_type"),
            tags=data.get("tags", []),
            context=data.get("context", {}),
        )
