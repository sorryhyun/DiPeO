"""Core types for diagram compilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from dipeo.diagram_generated import NodeID


class CompilationPhase(Enum):
    """Phases of diagram compilation."""

    VALIDATION = auto()
    NODE_TRANSFORMATION = auto()
    CONNECTION_RESOLUTION = auto()
    EDGE_BUILDING = auto()
    OPTIMIZATION = auto()
    ASSEMBLY = auto()


@dataclass
class CompilationError:
    """Represents a compilation error with context."""

    phase: CompilationPhase
    message: str
    node_id: NodeID | None = None
    arrow_id: str | None = None
    severity: str = "error"  # error, warning, info
    suggestion: str | None = None
    field_name: str | None = None

    def to_validation_result(self, as_warning: bool = False) -> Any:
        """Convert to ValidationError or ValidationWarning for compatibility.

        Args:
            as_warning: If True, return ValidationWarning; otherwise ValidationError

        Returns:
            ValidationError or ValidationWarning instance
        """
        field_name = self._compute_field_name()

        if as_warning:
            from dipeo.domain.base.validator import ValidationWarning

            return ValidationWarning(self.message, field_name=field_name)
        else:
            from dipeo.domain.base.exceptions import ValidationError

            return ValidationError(self.message)

    def _compute_field_name(self) -> str | None:
        """Compute field name from error context.

        Returns:
            Field name string or None if not computable
        """
        if self.field_name:
            return self.field_name
        if self.node_id:
            return f"node.{self.node_id}"
        if self.arrow_id:
            return f"arrow.{self.arrow_id}"
        return None

    # Backward compatibility methods
    def to_validation_error(self) -> Any:
        """Convert to ValidationError (deprecated: use to_validation_result)."""
        return self.to_validation_result(as_warning=False)

    def to_validation_warning(self) -> Any:
        """Convert to ValidationWarning (deprecated: use to_validation_result)."""
        return self.to_validation_result(as_warning=True)


@dataclass
class CompilationResult:
    """Result of diagram compilation with diagnostics."""

    diagram: Any | None  # ExecutableDiagram, avoiding circular import
    errors: list[CompilationError] = field(default_factory=list)
    warnings: list[CompilationError] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return self.diagram is not None and not self.errors

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    def add_error(self, phase: CompilationPhase, message: str, **kwargs: Any) -> None:
        self.errors.append(
            CompilationError(phase=phase, message=message, severity="error", **kwargs)
        )

    def add_warning(self, phase: CompilationPhase, message: str, **kwargs: Any) -> None:
        self.warnings.append(
            CompilationError(phase=phase, message=message, severity="warning", **kwargs)
        )
