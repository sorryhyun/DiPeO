"""Event type definitions and enums."""

from enum import Enum

# Re-export generated EventType as the single source of truth
from dipeo.diagram_generated.enums import EventType

__all__ = ["EventType", "EventPriority", "EventVersion"]


class EventPriority(Enum):
    """Priority levels for event processing."""
    
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventVersion(Enum):
    """Event schema versions for backward compatibility."""
    
    V1 = "1.0.0"
    V2 = "2.0.0"  # Current version