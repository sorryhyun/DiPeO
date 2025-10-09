"""Base classes for post-processing pipeline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class DiagramChangeType(Enum):
    """Types of changes made during diagram post-processing."""

    NODE_REMOVED = "node_removed"
    NODE_MERGED = "node_merged"
    NODE_MODIFIED = "node_modified"
    CONNECTION_REMOVED = "connection_removed"
    CONNECTION_MODIFIED = "connection_modified"
    CONNECTION_ADDED = "connection_added"
    METADATA_UPDATED = "metadata_updated"


@dataclass
class DiagramChange:
    """Represents a single change made during diagram processing."""

    change_type: DiagramChangeType
    description: str
    target: str  # Node label or connection identifier
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagramProcessingReport:
    """Report of changes made by a diagram processor."""

    processor_name: str
    changes: list[DiagramChange] = field(default_factory=list)
    nodes_removed: int = 0
    nodes_modified: int = 0
    connections_removed: int = 0
    connections_modified: int = 0
    connections_added: int = 0
    processing_time_ms: float = 0
    error: str | None = None

    def add_change(self, change: DiagramChange) -> None:
        """Add a change to the report and update counters."""
        self.changes.append(change)

        # Update counters based on change type
        if change.change_type == DiagramChangeType.NODE_REMOVED:
            self.nodes_removed += 1
        elif change.change_type == DiagramChangeType.NODE_MODIFIED:
            self.nodes_modified += 1
        elif change.change_type == DiagramChangeType.CONNECTION_REMOVED:
            self.connections_removed += 1
        elif change.change_type == DiagramChangeType.CONNECTION_MODIFIED:
            self.connections_modified += 1
        elif change.change_type == DiagramChangeType.CONNECTION_ADDED:
            self.connections_added += 1

    @property
    def total_changes(self) -> int:
        """Total number of changes made."""
        return len(self.changes)

    def has_changes(self) -> bool:
        """Check if any changes were made."""
        return self.total_changes > 0


class BaseDiagramProcessor(ABC):
    """Base class for all diagram post-processing processors."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize processor with optional configuration."""
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

    @property
    @abstractmethod
    def name(self) -> str:
        """Return processor name for reporting."""
        pass

    @abstractmethod
    def process_diagram(
        self, diagram: dict[str, Any]
    ) -> tuple[dict[str, Any], DiagramProcessingReport]:
        """
        Process the diagram and return modified version with report.

        Args:
            diagram: The diagram dictionary to process

        Returns:
            Tuple of (processed_diagram, report)
        """
        pass

    def is_applicable(self, diagram: dict[str, Any]) -> bool:
        """
        Check if this processor is applicable to the given diagram.

        Default implementation checks if processor is enabled and diagram has nodes.
        Subclasses can override for more specific checks.
        """
        if not self.enabled:
            return False

        # Must have nodes to process
        if "nodes" not in diagram or not diagram["nodes"]:
            return False

        return True

    def _clone_diagram(self, diagram: dict[str, Any]) -> dict[str, Any]:
        """Create a deep copy of the diagram for processing."""
        import copy

        return copy.deepcopy(diagram)


@dataclass
class DiagramPipelineReport:
    """Aggregated report from all processors in diagram pipeline."""

    processor_reports: list[DiagramProcessingReport] = field(default_factory=list)
    total_time_ms: float = 0
    diagram_stats: dict[str, Any] = field(default_factory=dict)

    def add_processor_report(self, report: DiagramProcessingReport) -> None:
        """Add a processor report to the pipeline report."""
        self.processor_reports.append(report)
        self.total_time_ms += report.processing_time_ms

    @property
    def total_changes(self) -> int:
        """Total changes across all processors."""
        return sum(r.total_changes for r in self.processor_reports)

    @property
    def total_nodes_removed(self) -> int:
        """Total nodes removed across all processors."""
        return sum(r.nodes_removed for r in self.processor_reports)

    @property
    def total_connections_modified(self) -> int:
        """Total connections modified across all processors."""
        return sum(
            r.connections_removed + r.connections_modified + r.connections_added
            for r in self.processor_reports
        )

    def has_changes(self) -> bool:
        """Check if any processor made changes."""
        return any(r.has_changes() for r in self.processor_reports)

    def get_summary(self) -> str:
        """Get a human-readable summary of the processing."""
        lines = ["Post-Processing Summary:"]
        lines.append(f"  Total processors run: {len(self.processor_reports)}")
        lines.append(f"  Total changes: {self.total_changes}")
        lines.append(f"  Nodes removed: {self.total_nodes_removed}")
        lines.append(f"  Connections modified: {self.total_connections_modified}")
        lines.append(f"  Processing time: {self.total_time_ms:.2f}ms")

        if self.has_changes():
            lines.append("\nChanges by processor:")
            for report in self.processor_reports:
                if report.has_changes():
                    lines.append(f"  - {report.processor_name}: {report.total_changes} changes")
                    if report.nodes_removed > 0:
                        lines.append(f"    • Removed {report.nodes_removed} nodes")
                    if report.connections_modified > 0:
                        lines.append(f"    • Modified {report.connections_modified} connections")
        else:
            lines.append("\nNo changes were made.")

        return "\n".join(lines)


# Backward compatibility aliases (deprecated)
ChangeType = DiagramChangeType
ProcessingChange = DiagramChange
ProcessingReport = DiagramProcessingReport
BaseProcessor = BaseDiagramProcessor
PipelineReport = DiagramPipelineReport


class BasePostProcessor(ABC):
    """Abstract base class for post-processing phase with standard interface."""

    @abstractmethod
    def process(
        self, diagram: dict[str, Any], config: Any | None = None
    ) -> tuple[dict[str, Any], DiagramPipelineReport]:
        """
        Standard interface: process a diagram and return optimized diagram with report.

        Args:
            diagram: The diagram to post-process
            config: Optional post-processing configuration

        Returns:
            Tuple of (optimized_diagram, processing_report)
        """
        pass
