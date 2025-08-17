"""Protocol for compiling between different diagram representations.

DEPRECATED: This module is kept for backward compatibility.
Use dipeo.domain.diagram.ports.DiagramCompiler instead.

This module provides a protocol that diagram compilers must implement.
The actual implementation lives in the application layer.
"""

from typing import Protocol, TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from dipeo.diagram_generated import DomainDiagram
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram

# Import from new location for backward compatibility
from dipeo.domain.diagram.ports import DiagramCompiler as _DomainDiagramCompiler


class DiagramCompiler(Protocol):
    """Protocol for diagram compilation.
    
    DEPRECATED: Use dipeo.domain.diagram.ports.DiagramCompiler instead.
    This class is kept for backward compatibility only.
    
    Note: The primary implementation is StandardCompiler
    in dipeo.application.compilation.standard_compiler
    """
    
    def compile(self, domain_diagram: "DomainDiagram") -> "ExecutableDiagram":
        """Compile domain diagram to executable form with resolved connections and execution order."""
        ...


# Re-export the domain version for convenience
DiagramCompilerV2 = _DomainDiagramCompiler

def __getattr__(name):
    """Provide deprecation warnings for old imports."""
    if name == "DiagramCompiler":
        warnings.warn(
            "Importing DiagramCompiler from dipeo.core.ports.diagram_compiler is deprecated. "
            "Use dipeo.domain.diagram.ports.DiagramCompiler instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return DiagramCompiler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    
