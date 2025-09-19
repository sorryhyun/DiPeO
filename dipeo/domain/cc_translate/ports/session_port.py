"""Protocol for session abstraction in domain layer."""

from datetime import datetime
from typing import Optional, Protocol


class SessionPort(Protocol):
    """Abstract interface for session data access."""

    @property
    def session_id(self) -> str:
        """Get the session identifier."""
        ...

    @property
    def events(self) -> list:
        """Get all events in the session."""
        ...

    @property
    def metadata(self) -> dict:
        """Get session metadata."""
        ...

    @property
    def start_time(self) -> Optional[datetime]:
        """Get session start time."""
        ...

    @property
    def end_time(self) -> Optional[datetime]:
        """Get session end time."""
        ...

    def get_event_count(self) -> int:
        """Get total number of events."""
        ...

    def get_tool_usage_stats(self) -> dict[str, int]:
        """Get tool usage statistics."""
        ...

    def to_dict(self) -> dict:
        """Convert session to dictionary representation."""
        ...
