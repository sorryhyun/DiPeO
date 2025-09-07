"""Runtime data structures for resolution system.

This module provides value objects and data structures used during
runtime input resolution.
"""

from dataclasses import dataclass, field
from typing import Any

from dipeo.diagram_generated import NodeID
from dipeo.diagram_generated.enums import ContentType


@dataclass
class InputResolutionContext:
    """Context provided during input resolution.

    This context carries all the information needed to resolve
    inputs for a node during execution.
    """

    target_node_id: NodeID
    target_input_name: str
    node_outputs: dict[NodeID, Any]
    execution_order: list[NodeID] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_output(self, node_id: NodeID) -> bool:
        """Check if a node has produced output."""
        return node_id in self.node_outputs

    def get_output(self, node_id: NodeID, default: Any = None) -> Any:
        """Get output from a node, with optional default."""
        return self.node_outputs.get(node_id, default)


@dataclass
class TransformationContext:
    """Context for data transformation operations."""

    source_node_id: NodeID | None = None
    target_node_id: NodeID | None = None
    source_content_type: ContentType | None = None
    target_content_type: ContentType | None = None
    source_output_name: str | None = None
    target_input_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of input validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True)

    @classmethod
    def failure(cls, error: str) -> "ValidationResult":
        """Create a failed validation result with an error."""
        return cls(is_valid=False, errors=[error])


@dataclass
class ResolutionPath:
    """Represents the path taken to resolve an input value.

    This is useful for debugging and understanding how values
    flow through the diagram.
    """

    steps: list["ResolutionStep"] = field(default_factory=list)

    def add_step(self, step: "ResolutionStep") -> None:
        """Add a step to the resolution path."""
        self.steps.append(step)

    def to_string(self) -> str:
        """Convert the path to a human-readable string."""
        if not self.steps:
            return "No resolution steps"
        return " -> ".join(str(step) for step in self.steps)


@dataclass
class ResolutionStep:
    """A single step in the resolution path."""

    step_type: str  # e.g., "connection", "default", "transformation"
    description: str
    source_node_id: NodeID | None = None
    target_node_id: NodeID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        if self.source_node_id and self.target_node_id:
            return f"{self.step_type}: {self.source_node_id} -> {self.target_node_id} ({self.description})"
        return f"{self.step_type}: {self.description}"
