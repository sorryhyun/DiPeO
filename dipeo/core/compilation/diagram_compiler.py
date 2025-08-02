"""Protocol for compiling between different diagram representations.

This module provides a protocol that diagram compilers must implement.
The actual implementation is now interface-based and lives in the application layer.
"""

from typing import Protocol

from dipeo.models import DomainDiagram

from dipeo.core.compilation.executable_diagram import ExecutableDiagram


class DiagramCompiler(Protocol):
    """Protocol for diagram compilation.
    
    Note: The primary implementation is InterfaceBasedDiagramCompiler
    in dipeo.application.resolution.interface_based_compiler
    """
    
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile domain diagram to executable form with resolved connections and execution order."""
        ...
    
