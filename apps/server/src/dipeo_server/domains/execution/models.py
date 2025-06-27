"""Models for execution domain."""

from typing import Any

from dipeo_domain import DomainDiagram
from pydantic import BaseModel, Field


class ExecutionHint(BaseModel):
    """Hint for execution dependencies."""

    source: str
    variable: str = "flow"


class ExecutionHints(BaseModel):
    """Collection of execution hints for the engine."""

    start_nodes: list[str] = Field(default_factory=list)
    person_nodes: dict[str, str] = Field(default_factory=dict)  # node_id -> person_id
    node_dependencies: dict[str, list[ExecutionHint]] = Field(default_factory=dict)


class ExecutionReadyDiagram(BaseModel):
    """Diagram ready for execution with all required data."""

    diagram_id: str
    backend_format: dict[str, Any]
    api_keys: dict[str, str]
    execution_hints: ExecutionHints
    domain_model: DomainDiagram | None = None

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_dict(
        cls,
        diagram_id: str,
        backend_format: dict[str, Any],
        api_keys: dict[str, str],
        execution_hints: dict[str, Any],
        domain_model: DomainDiagram | None = None,
    ) -> "ExecutionReadyDiagram":
        """Create from dict data."""
        hints = (
            ExecutionHints(**execution_hints)
            if isinstance(execution_hints, dict)
            else execution_hints
        )
        return cls(
            diagram_id=diagram_id,
            backend_format=backend_format,
            api_keys=api_keys,
            execution_hints=hints,
            domain_model=domain_model,
        )
