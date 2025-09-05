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
    """Collect validation diagnostics using the domain compiler.

    This function uses the domain compiler as the single source of truth for
    validation, ensuring consistency across the entire system.

    Args:
        diagram: The domain diagram to validate
        stop_after: Optional phase to stop after (defaults to all phases)

    Returns:
        CompilationResult with errors and warnings
    """
    compiler = DomainDiagramCompiler()

    # If not specified, just run validation phase for pure validation
    if stop_after is None:
        stop_after = CompilationPhase.VALIDATION

    return compiler.compile_with_diagnostics(diagram, stop_after=stop_after)


def validate_diagram(diagram: DomainDiagram) -> CompilationResult:
    """Validate a diagram through all compilation phases.

    This performs a full compilation to catch all possible errors,
    not just structural validation.

    Args:
        diagram: The domain diagram to validate

    Returns:
        CompilationResult with complete diagnostics
    """
    compiler = DomainDiagramCompiler()
    return compiler.compile_with_diagnostics(diagram)


def validate_structure_only(diagram: DomainDiagram) -> CompilationResult:
    """Validate only the structural aspects of a diagram.

    This stops after the validation phase, checking for:
    - Missing nodes
    - Duplicate IDs
    - Invalid node types
    - Basic structural integrity

    Args:
        diagram: The domain diagram to validate

    Returns:
        CompilationResult with structural validation results
    """
    return collect_diagnostics(diagram, stop_after=CompilationPhase.VALIDATION)


def validate_connections(diagram: DomainDiagram) -> CompilationResult:
    """Validate diagram including connection resolution.

    This validates through the connection resolution phase, checking:
    - All structural validation
    - Node transformation
    - Arrow/handle resolution
    - Connection validity

    Args:
        diagram: The domain diagram to validate

    Returns:
        CompilationResult with connection validation results
    """
    return collect_diagnostics(diagram, stop_after=CompilationPhase.CONNECTION_RESOLUTION)
