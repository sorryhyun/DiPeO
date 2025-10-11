"""Base classes and interfaces for compilation phases."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from dipeo.diagram_generated import DomainDiagram, NodeID
from dipeo.diagram_generated.generated_nodes import ExecutableNode
from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2

from ..types import CompilationPhase, CompilationResult


@dataclass
class CompilationContext:
    """Context passed through compilation phases.

    This context holds all intermediate state during diagram compilation,
    including inputs, outputs from each phase, and metadata.
    """

    domain_diagram: DomainDiagram
    result: CompilationResult = field(default_factory=lambda: CompilationResult(diagram=None))

    # Phase outputs
    nodes_list: list[Any] = field(default_factory=list)
    arrows_list: list[Any] = field(default_factory=list)
    typed_nodes: list[ExecutableNode] = field(default_factory=list)
    node_map: dict[NodeID, ExecutableNode] = field(default_factory=dict)
    resolved_connections: list[Any] = field(default_factory=list)
    typed_edges: list[ExecutableEdgeV2] = field(default_factory=list)

    # Metadata
    start_nodes: set[NodeID] = field(default_factory=set)
    person_nodes: dict[str, list[NodeID]] = field(default_factory=dict)
    node_dependencies: dict[NodeID, set[NodeID]] = field(default_factory=dict)


class PhaseInterface(ABC):
    """Interface for compilation phases.

    Each phase is responsible for a specific part of the compilation process
    and can report errors/warnings through the CompilationContext.
    """

    @abstractmethod
    def execute(self, context: CompilationContext) -> None:
        """Execute this compilation phase.

        Args:
            context: The compilation context containing all state

        The phase should:
        1. Read inputs from the context
        2. Perform its specific transformation/validation
        3. Write outputs back to the context
        4. Report any errors/warnings through context.result
        """
        pass

    @property
    @abstractmethod
    def phase_type(self) -> CompilationPhase:
        """Return the phase type for error reporting."""
        pass
