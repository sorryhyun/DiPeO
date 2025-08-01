"""Protocol for compiling between different diagram representations."""

from typing import Protocol

from dipeo.models import DomainDiagram

from .executable_diagram import ExecutableDiagram


class DiagramCompiler(Protocol):
    
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile domain diagram to executable form with resolved connections and execution order."""
        ...
    
