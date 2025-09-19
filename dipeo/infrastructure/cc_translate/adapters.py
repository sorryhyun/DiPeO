"""Infrastructure adapters for converting Claude Code sessions to domain models.

This module provides adapters to convert between infrastructure layer
types (like ClaudeCodeSession) and domain layer ports/models.
"""

from datetime import datetime
from typing import Optional

from .session_parser import ClaudeCodeSession


class SessionAdapter:
    """Adapter to convert ClaudeCodeSession to SessionPort interface.

    This adapter allows infrastructure types to be used with domain
    layer components that expect SessionPort protocol.
    """

    def __init__(self, session: ClaudeCodeSession):
        """Initialize the adapter with an infrastructure session.

        Args:
            session: The infrastructure ClaudeCodeSession to adapt
        """
        self._session = session

    @property
    def session_id(self) -> str:
        """Get the session identifier."""
        return self._session.session_id

    @property
    def events(self) -> list:
        """Get all events in the session."""
        return self._session.events

    @property
    def metadata(self) -> dict:
        """Get session metadata."""
        return self._session.metadata

    @property
    def start_time(self) -> Optional[datetime]:
        """Get session start time."""
        if hasattr(self._session.metadata, "start_time"):
            return self._session.metadata.start_time
        return None

    @property
    def end_time(self) -> Optional[datetime]:
        """Get session end time."""
        if hasattr(self._session.metadata, "end_time"):
            return self._session.metadata.end_time
        return None

    def get_event_count(self) -> int:
        """Get total number of events."""
        return len(self._session.events)

    def get_tool_usage_stats(self) -> dict[str, int]:
        """Get tool usage statistics."""
        return self._session.extract_tool_usage()

    def to_dict(self) -> dict:
        """Convert session to dictionary representation."""
        # Convert to a dictionary format compatible with domain expectations
        return {
            "session_id": self.session_id,
            "event_count": self.get_event_count(),
            "tool_usage": self.get_tool_usage_stats(),
            "events": [self._event_to_dict(e) for e in self.events],
            "metadata": self._metadata_to_dict(),
        }

    def _event_to_dict(self, event) -> dict:
        """Convert an event to dictionary."""
        return {
            "type": event.type,
            "uuid": event.uuid,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "tool_name": event.tool_name,
            "tool_input": event.tool_input,
            "tool_results": event.tool_results,
            "message": event.message,
        }

    def _metadata_to_dict(self) -> dict:
        """Convert metadata to dictionary."""
        meta = self._session.metadata
        return {
            "session_id": meta.session_id,
            "start_time": meta.start_time.isoformat() if meta.start_time else None,
            "end_time": meta.end_time.isoformat() if meta.end_time else None,
            "event_count": meta.event_count,
            "tool_usage_count": meta.tool_usage_count,
            "file_operations": meta.file_operations,
        }
