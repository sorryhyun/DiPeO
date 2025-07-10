"""Protocol for compiling between different diagram representations."""

from typing import Protocol, Dict, Any, List
from dipeo.models import DomainDiagram
from .executable_diagram import ExecutableDiagram


class DiagramCompiler(Protocol):
    """Compiles between domain and executable diagram representations."""
    
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
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
    
    def decompile(self, executable_diagram: ExecutableDiagram) -> DomainDiagram:
        """Convert an executable diagram back to domain representation.
        
        This is useful for:
        - Serialization and persistence
        - Editing compiled diagrams
        - Debugging and visualization
        
        Args:
            executable_diagram: The compiled diagram
            
        Returns:
            DomainDiagram representation
        """
        ...


class DiagramValidator(Protocol):
    """Validates diagram structure and semantics."""
    
    def validate_structure(self, diagram: Dict[str, Any]) -> List[str]:
        """Validate the structural integrity of a diagram.
        
        Checks:
        - Required nodes (start nodes)
        - Node connectivity
        - Circular dependencies
        - Handle references
        
        Args:
            diagram: The diagram to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        ...
    
    def validate_node(self, node: Dict[str, Any], node_type: str) -> List[str]:
        """Validate a specific node's configuration.
        
        Args:
            node: The node configuration
            node_type: The type of the node
            
        Returns:
            List of validation errors for this node
        """
        ...
    
    def validate_connections(self, nodes: List[Dict[str, Any]], 
                           arrows: List[Dict[str, Any]]) -> List[str]:
        """Validate connections between nodes.
        
        Args:
            nodes: List of nodes in the diagram
            arrows: List of arrows connecting nodes
            
        Returns:
            List of connection validation errors
        """
        ...