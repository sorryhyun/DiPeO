"""Protocol for compiling between different diagram representations."""

from typing import Protocol

from dipeo.models import Diagram

from .executable_diagram import ExecutableDiagram


class DiagramCompiler(Protocol):
    """Compiles between domain and executable diagram representations."""
    
    def compile(self, domain_diagram: Diagram) -> ExecutableDiagram:
        """Compile a domain diagram into an executable representation.
        
        This involves:
        - Resolving handle references to concrete node connections
        - Transforming arrows into executable edges
        - Calculating execution order
        - Validating the diagram structure
        
        Args:
            domain_diagram: The high-level domain diagram
            
        Returns:
            ExecutableDiagram ready for execution
            
        Raises:
            ValidationError: If the diagram cannot be compiled
        """
        ...
    
