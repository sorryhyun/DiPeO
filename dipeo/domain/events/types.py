"""Event type definitions and enums."""

from enum import Enum, auto


class EventType(Enum):
    """Types of domain events."""
    
    # Execution lifecycle
    EXECUTION_STARTED = auto()
    EXECUTION_COMPLETED = auto()
    EXECUTION_ERROR = auto()
    EXECUTION_STATUS_CHANGED = auto()
    
    # Node lifecycle
    NODE_STARTED = auto()
    NODE_COMPLETED = auto()
    NODE_ERROR = auto()
    NODE_OUTPUT = auto()
    NODE_STATUS_CHANGED = auto()
    
    # Metrics and monitoring
    METRICS_COLLECTED = auto()
    OPTIMIZATION_SUGGESTED = auto()
    
    # External integrations
    WEBHOOK_RECEIVED = auto()
    
    # Logging
    EXECUTION_LOG = auto()


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