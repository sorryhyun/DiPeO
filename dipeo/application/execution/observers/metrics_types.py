"""Data classes for execution metrics collection and analysis."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NodeMetrics:
    """Metrics for a single node execution."""

    node_id: str
    node_type: str
    start_time: float
    end_time: float | None = None
    duration_ms: float | None = None
    memory_usage: int | None = None
    token_usage: dict[str, int] | None = None
    error: str | None = None
    iteration: int | None = None
    dependencies: set[str] = field(default_factory=set)
    module_timings: dict[str, float] = field(default_factory=dict)


@dataclass
class ExecutionMetrics:
    """Metrics for an entire diagram execution."""

    execution_id: str
    start_time: float
    end_time: float | None = None
    total_duration_ms: float | None = None
    node_metrics: dict[str, NodeMetrics] = field(default_factory=dict)
    critical_path: list[str] = field(default_factory=list)
    parallelizable_groups: list[list[str]] = field(default_factory=list)
    bottlenecks: list[str] = field(default_factory=list)


@dataclass
class DiagramOptimization:
    """Optimization suggestions for diagram execution."""

    execution_id: str
    diagram_id: str | None
    bottlenecks: list[dict[str, Any]]
    parallelizable: list[list[str]]
    suggested_changes: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "execution_id": self.execution_id,
            "diagram_id": self.diagram_id,
            "bottlenecks": self.bottlenecks,
            "parallelizable": self.parallelizable,
            "suggested_changes": self.suggested_changes,
        }
