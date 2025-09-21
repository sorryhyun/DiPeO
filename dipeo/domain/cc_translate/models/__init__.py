"""Domain models for cc_translate module."""

from .event import (
    DomainEvent,
    EventContent,
    EventRole,
    EventType,
    ToolInfo,
)
from .preprocessed import (
    ChangeType,
    ConversionMapping,
    PreprocessedData,
    ProcessingChange,
    ProcessingStage,
    ProcessingStats,
)
from .session import DomainSession, SessionMetadata, SessionStatus

__all__ = [
    "ChangeType",
    "ConversionMapping",
    # Event models
    "DomainEvent",
    # Session models
    "DomainSession",
    "EventContent",
    "EventRole",
    "EventType",
    # Preprocessed data models
    "PreprocessedData",
    "ProcessingChange",
    "ProcessingStage",
    "ProcessingStats",
    "SessionMetadata",
    "SessionStatus",
    "ToolInfo",
]
