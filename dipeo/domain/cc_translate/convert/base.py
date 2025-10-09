"""Base classes and interfaces for the convert module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

# Removed dependency on generated code - domain should not depend on generated
from dipeo.domain.cc_translate.models.preprocessed import PreprocessedData


class ConversionStatus(Enum):
    """Status of a conversion process."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class ConversionMetrics:
    """Metrics for tracking conversion performance."""

    nodes_processed: int = 0
    connections_processed: int = 0
    nodes_created: int = 0
    connections_created: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def duration_seconds(self) -> float | None:
        """Calculate the duration of conversion in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def has_errors(self) -> bool:
        """Check if there were any errors during conversion."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there were any warnings during conversion."""
        return len(self.warnings) > 0


@dataclass
class ConversionContext:
    """Context information for tracking conversion state."""

    session_id: str
    conversion_id: str
    status: ConversionStatus = ConversionStatus.PENDING
    metrics: ConversionMetrics = field(default_factory=ConversionMetrics)
    metadata: dict[str, Any] = field(default_factory=dict)
    current_node_id: str | None = None
    current_connection_id: str | None = None

    def start(self) -> None:
        """Mark the conversion as started."""
        self.status = ConversionStatus.IN_PROGRESS
        self.metrics.start_time = datetime.now()

    def complete(self, success: bool = True) -> None:
        """Mark the conversion as completed."""
        self.metrics.end_time = datetime.now()
        if success:
            self.status = ConversionStatus.SUCCESS
        elif self.metrics.nodes_created > 0:
            self.status = ConversionStatus.PARTIAL
        else:
            self.status = ConversionStatus.FAILED

    def add_warning(self, message: str) -> None:
        """Add a warning to the conversion context."""
        self.metrics.warnings.append(message)

    def add_error(self, message: str) -> None:
        """Add an error to the conversion context."""
        self.metrics.errors.append(message)


@dataclass
class ConversionReport:
    """Report of the conversion process."""

    session_id: str
    conversion_id: str
    status: ConversionStatus
    diagram: dict[str, Any] | None
    metrics: ConversionMetrics
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if the conversion was successful."""
        return self.status == ConversionStatus.SUCCESS

    @property
    def partial_success(self) -> bool:
        """Check if the conversion was partially successful."""
        return self.status == ConversionStatus.PARTIAL

    def to_dict(self) -> dict[str, Any]:
        """Convert the report to a dictionary."""
        return {
            "session_id": self.session_id,
            "conversion_id": self.conversion_id,
            "status": self.status.value,
            "diagram_created": self.diagram is not None,
            "metrics": {
                "nodes_processed": self.metrics.nodes_processed,
                "connections_processed": self.metrics.connections_processed,
                "nodes_created": self.metrics.nodes_created,
                "connections_created": self.metrics.connections_created,
                "warnings": self.metrics.warnings,
                "errors": self.metrics.errors,
                "duration_seconds": self.metrics.duration_seconds,
            },
            "metadata": self.metadata,
        }


class BaseConverter(ABC):
    """Abstract base class for converters."""

    @abstractmethod
    def convert(
        self,
        preprocessed_data: PreprocessedData,
        context: ConversionContext | None = None,
    ) -> ConversionReport:
        """
        Convert preprocessed data into a diagram.

        Args:
            preprocessed_data: The preprocessed session data to convert
            context: Optional conversion context for tracking

        Returns:
            A ConversionReport containing the result and metrics
        """
        pass

    @abstractmethod
    def validate_input(self, preprocessed_data: PreprocessedData) -> bool:
        """
        Validate that the input data can be converted.

        Args:
            preprocessed_data: The preprocessed data to validate

        Returns:
            True if the data is valid for conversion, False otherwise
        """
        pass

    def create_context(self, session_id: str) -> ConversionContext:
        """
        Create a new conversion context.

        Args:
            session_id: The session ID for the conversion

        Returns:
            A new ConversionContext instance
        """
        import uuid

        return ConversionContext(
            session_id=session_id,
            conversion_id=str(uuid.uuid4()),
        )

    def process(
        self, preprocessed_data: PreprocessedData, config: Any | None = None
    ) -> tuple[dict, ConversionReport]:
        """
        Standard interface: process preprocessed data and return diagram with report.

        This is a wrapper around convert() to provide consistent interface across phases.

        Args:
            preprocessed_data: The preprocessed session data to convert
            config: Optional conversion configuration (currently unused)

        Returns:
            Tuple of (diagram, conversion_report)
        """
        report = self.convert(preprocessed_data)
        diagram = report.diagram if report.diagram else {}
        return diagram, report
