"""Protocol for event abstraction in domain layer."""

from datetime import datetime
from typing import Any, Optional, Protocol


class EventPort(Protocol):
    """Abstract interface for session events."""

    @property
    def type(self) -> str:
        """Get event type (user/assistant/summary)."""
        ...

    @property
    def uuid(self) -> str:
        """Get event unique identifier."""
        ...

    @property
    def timestamp(self) -> datetime:
        """Get event timestamp."""
        ...

    @property
    def message(self) -> dict[str, Any]:
        """Get event message content."""
        ...

    @property
    def parent_uuid(self) -> Optional[str]:
        """Get parent event UUID if exists."""
        ...

    @property
    def tool_name(self) -> Optional[str]:
        """Get tool name if this is a tool use event."""
        ...

    @property
    def tool_input(self) -> Optional[dict[str, Any]]:
        """Get tool input parameters if applicable."""
        ...

    @property
    def tool_results(self) -> list[dict[str, Any]]:
        """Get tool execution results."""
        ...

    @property
    def role(self) -> Optional[str]:
        """Get role from message (user/assistant/system)."""
        ...

    @property
    def is_meta(self) -> bool:
        """Check if this is a meta/system event."""
        ...

    def has_tool_use(self) -> bool:
        """Check if event contains tool usage."""
        ...

    def to_dict(self) -> dict:
        """Convert event to dictionary representation."""
        ...
