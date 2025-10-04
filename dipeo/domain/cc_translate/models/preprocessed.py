"""Domain model for preprocessed data."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .event import DomainEvent
from .session import DomainSession


class ProcessingStage(Enum):
    """Processing stage enumeration."""

    INITIAL = "initial"
    PREPROCESSED = "preprocessed"
    CONVERTED = "converted"
    POSTPROCESSED = "postprocessed"
    COMPLETED = "completed"


class ChangeType(Enum):
    """Type of change made during processing."""

    EVENT_PRUNED = "event_pruned"
    FIELD_REMOVED = "field_removed"
    EVENT_MODIFIED = "event_modified"
    EVENT_MERGED = "event_merged"
    METADATA_UPDATED = "metadata_updated"
    STRUCTURE_OPTIMIZED = "structure_optimized"


@dataclass
class ProcessingChange:
    """Record of a change made during processing."""

    stage: ProcessingStage
    change_type: ChangeType
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    target_id: str | None = None  # Event UUID or other identifier
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "stage": self.stage.value,
            "change_type": self.change_type.value,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "target_id": self.target_id,
            "details": self.details,
        }


@dataclass
class ProcessingStats:
    """Statistics about the processing."""

    total_events_input: int = 0
    total_events_output: int = 0
    events_pruned: int = 0
    events_modified: int = 0
    fields_removed: int = 0
    processing_time_ms: int | None = None
    memory_usage_mb: float | None = None

    def get_reduction_ratio(self) -> float:
        """Calculate the reduction ratio."""
        if self.total_events_input == 0:
            return 0.0
        return 1.0 - (self.total_events_output / self.total_events_input)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_events_input": self.total_events_input,
            "total_events_output": self.total_events_output,
            "events_pruned": self.events_pruned,
            "events_modified": self.events_modified,
            "fields_removed": self.fields_removed,
            "reduction_ratio": self.get_reduction_ratio(),
            "processing_time_ms": self.processing_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
        }


@dataclass
class ConversionMapping:
    """Mapping between source and converted elements."""

    source_id: str
    target_id: str
    element_type: str  # event, node, connection
    transformation: str  # type of transformation applied
    confidence: float = 1.0  # confidence in the mapping

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "element_type": self.element_type,
            "transformation": self.transformation,
            "confidence": self.confidence,
        }


@dataclass
class PreprocessedData:
    """Domain model for preprocessed session data."""

    # Core data
    session: DomainSession
    stage: ProcessingStage = ProcessingStage.INITIAL

    # Processing tracking
    changes: list[ProcessingChange] = field(default_factory=list)
    stats: ProcessingStats = field(default_factory=ProcessingStats)
    mappings: list[ConversionMapping] = field(default_factory=list)

    # Processing metadata
    processing_config: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Processed artifacts
    processed_events: list[DomainEvent] = field(default_factory=list)
    conversation_context: dict[str, Any] = field(default_factory=dict)
    extracted_patterns: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize processed events from session if not set."""
        if not self.processed_events and self.session.events:
            self.processed_events = self.session.events.copy()
            self.stats.total_events_input = len(self.session.events)
            self.stats.total_events_output = len(self.processed_events)

    def validate(self) -> list[str]:
        """Validate preprocessed data integrity."""
        errors = []

        # Validate session
        session_errors = self.session.validate()
        errors.extend([f"Session: {e}" for e in session_errors])

        # Validate stats consistency
        if self.stats.events_pruned > self.stats.total_events_input:
            errors.append("Events pruned cannot exceed total input events")

        if self.stats.total_events_output > self.stats.total_events_input:
            errors.append("Output events cannot exceed input events without merging")

        # Validate mappings
        for mapping in self.mappings:
            if mapping.confidence < 0 or mapping.confidence > 1:
                errors.append(f"Invalid confidence value: {mapping.confidence}")

        return errors

    def add_change(
        self,
        change_type: ChangeType,
        description: str,
        target_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Record a processing change."""
        change = ProcessingChange(
            stage=self.stage,
            change_type=change_type,
            description=description,
            target_id=target_id,
            details=details or {},
        )
        self.changes.append(change)

    def add_mapping(
        self,
        source_id: str,
        target_id: str,
        element_type: str,
        transformation: str,
        confidence: float = 1.0,
    ) -> None:
        """Add a conversion mapping."""
        mapping = ConversionMapping(
            source_id=source_id,
            target_id=target_id,
            element_type=element_type,
            transformation=transformation,
            confidence=confidence,
        )
        self.mappings.append(mapping)

    def update_stage(self, new_stage: ProcessingStage) -> None:
        """Update the processing stage."""
        self.stage = new_stage

    def prune_event(self, event_uuid: str, reason: str) -> bool:
        """Prune an event from processed events."""
        initial_count = len(self.processed_events)
        self.processed_events = [e for e in self.processed_events if e.uuid != event_uuid]

        if len(self.processed_events) < initial_count:
            self.stats.events_pruned += 1
            self.stats.total_events_output = len(self.processed_events)
            self.add_change(
                ChangeType.EVENT_PRUNED,
                f"Pruned event: {reason}",
                target_id=event_uuid,
            )
            return True
        return False

    def get_processing_summary(self) -> dict:
        """Get a summary of the processing."""
        return {
            "session_id": self.session.session_id,
            "stage": self.stage.value,
            "stats": self.stats.to_dict(),
            "total_changes": len(self.changes),
            "total_mappings": len(self.mappings),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "change_summary": {
                change_type.value: sum(1 for c in self.changes if c.change_type == change_type)
                for change_type in ChangeType
            },
        }

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "session": self.session.to_dict(),
            "stage": self.stage.value,
            "changes": [c.to_dict() for c in self.changes],
            "stats": self.stats.to_dict(),
            "mappings": [m.to_dict() for m in self.mappings],
            "processing_config": self.processing_config,
            "errors": self.errors,
            "warnings": self.warnings,
            "processed_events": [
                e.to_dict() if hasattr(e, "to_dict") else str(e) for e in self.processed_events
            ],
            "conversation_context": self.conversation_context,
            "extracted_patterns": self.extracted_patterns,
        }
