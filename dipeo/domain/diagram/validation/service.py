"""Domain validation service using the compiler as the single source of truth."""

from __future__ import annotations

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.compilation.domain_compiler import (
    CompilationPhase,
    CompilationResult,
    DomainDiagramCompiler,
)


def collect_diagnostics(
    diagram: DomainDiagram, stop_after: CompilationPhase | None = None
) -> CompilationResult:
    """Collect validation diagnostics using the domain compiler as single source of truth."""
    compiler = DomainDiagramCompiler()

    if stop_after is None:
        stop_after = CompilationPhase.VALIDATION

    return compiler.compile_with_diagnostics(diagram, stop_after=stop_after)


def validate_diagram(diagram: DomainDiagram) -> CompilationResult:
    """Perform full compilation to catch all possible errors, not just structural validation."""
    compiler = DomainDiagramCompiler()
    return compiler.compile_with_diagnostics(diagram)


def validate_structure_only(diagram: DomainDiagram) -> CompilationResult:
    """Validate structural aspects: missing nodes, duplicate IDs, invalid types, basic integrity."""
    return collect_diagnostics(diagram, stop_after=CompilationPhase.VALIDATION)


def validate_connections(diagram: DomainDiagram) -> CompilationResult:
    """Validate through connection resolution phase: structure, transformation, handles, validity."""
    return collect_diagnostics(diagram, stop_after=CompilationPhase.CONNECTION_RESOLUTION)
