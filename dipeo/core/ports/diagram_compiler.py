"""Protocol for compiling between different diagram representations.

This module provides a protocol that diagram compilers must implement.
The actual implementation lives in the application layer.
"""

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from dipeo.models import DomainDiagram
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram


class DiagramCompiler(Protocol):
    """Protocol for diagram compilation.
    
    Note: The primary implementation is StandardCompiler
    in dipeo.application.compilation.standard_compiler
    """
    
    def compile(self, domain_diagram: "DomainDiagram") -> "ExecutableDiagram":
        """Compile domain diagram to executable form with resolved connections and execution order."""
        ...
    
