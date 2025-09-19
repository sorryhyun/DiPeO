"""Base classes and types for session preprocessing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from dipeo.domain.cc_translate.models.session import DomainSession


class SessionChangeType(Enum):
    """Types of changes that can be made to a session during preprocessing."""

    EVENT_PRUNED = "event_pruned"
    FIELD_REMOVED = "field_removed"
    CONTENT_MODIFIED = "content_modified"
    EVENT_MERGED = "event_merged"
    METADATA_UPDATED = "metadata_updated"
    STRUCTURE_REORGANIZED = "structure_reorganized"


@dataclass
class SessionChange:
    """Represents a single change made to a session during preprocessing."""

    change_type: SessionChangeType
    description: str
    target: str  # What was changed (e.g., "event_123", "field:content")
    details: Optional[dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"[{self.change_type.value}] {self.description} (target: {self.target})"


@dataclass
class SessionProcessingReport:
    """Report of all changes made during session preprocessing."""

    session_id: str
    changes: list[SessionChange] = field(default_factory=list)
    total_events_before: int = 0
    total_events_after: int = 0
    processing_time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_change(self, change: SessionChange) -> None:
        """Add a change to the report."""
        self.changes.append(change)

    def add_error(self, error: str) -> None:
        """Add an error to the report."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning to the report."""
        self.warnings.append(warning)

    @property
    def total_changes(self) -> int:
        """Get total number of changes made."""
        return len(self.changes)

    @property
    def has_errors(self) -> bool:
        """Check if processing had errors."""
        return len(self.errors) > 0

    @property
    def events_pruned_count(self) -> int:
        """Count of events that were pruned."""
        return sum(1 for c in self.changes if c.change_type == SessionChangeType.EVENT_PRUNED)

    @property
    def fields_removed_count(self) -> int:
        """Count of fields that were removed."""
        return sum(1 for c in self.changes if c.change_type == SessionChangeType.FIELD_REMOVED)

    def get_summary(self) -> str:
        """Get a summary of the processing results."""
        lines = [
            f"Session Processing Report for {self.session_id}",
            f"  Events: {self.total_events_before} → {self.total_events_after}",
            f"  Total changes: {self.total_changes}",
            f"  Events pruned: {self.events_pruned_count}",
            f"  Fields removed: {self.fields_removed_count}",
            f"  Processing time: {self.processing_time_ms:.2f}ms",
        ]

        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
        if self.warnings:
            lines.append(f"  Warnings: {len(self.warnings)}")

        return "\n".join(lines)


class BaseSessionProcessor(ABC):
    """Abstract base class for all session processors in the preprocess phase."""

    def __init__(self, config: Optional[Any] = None):
        """Initialize processor with optional configuration."""
        self.config = config or self._get_default_config()

    @abstractmethod
    def _get_default_config(self) -> Any:
        """Get default configuration for this processor."""
        pass

    @abstractmethod
    def process_session(
        self, session: DomainSession
    ) -> tuple[DomainSession, SessionProcessingReport]:
        """Process a session and return the processed session with a report.

        Args:
            session: The session to process

        Returns:
            Tuple of (processed_session, processing_report)
        """
        pass

    def validate_session(self, session: DomainSession) -> list[str]:
        """Validate that a session can be processed.

        Args:
            session: The session to validate

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        if session is None:
            errors.append("Session cannot be None")
        elif not hasattr(session, "id"):
            errors.append("Session must have an id attribute")
        elif not hasattr(session, "events"):
            errors.append("Session must have an events attribute")

        return errors

    def _create_report(self, session: DomainSession) -> SessionProcessingReport:
        """Create a new processing report for a session."""
        return SessionProcessingReport(
            session_id=getattr(session, "id", "unknown"),
            total_events_before=len(getattr(session, "events", [])),
        )
