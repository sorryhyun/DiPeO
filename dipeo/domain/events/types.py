"""Event type definitions and enums."""

from enum import Enum

from dipeo.diagram_generated.enums import EventPriority, EventType

__all__ = ["EventPriority", "EventType", "EventVersion"]


class EventVersion(Enum):
    """Event schema versions for backward compatibility."""

    V1 = "1.0.0"
    V2 = "2.0.0"
