"""Use case for compiling diagrams."""

from typing import Optional

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.domain.diagram.ports import DiagramCompiler


class CompileDiagramUseCase:
    """Use case for compiling domain diagrams to executable form.
    
    This use case handles:
    - Compiling domain diagrams to executable diagrams
    - Resolving connections and dependencies
    - Calculating execution order
    """
    
    def __init__(self, diagram_compiler: DiagramCompiler):
        """Initialize the use case with required dependencies.
        
        Args:
            diagram_compiler: Compiler for transforming diagrams
        """
        self.diagram_compiler = diagram_compiler
    
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile a domain diagram to executable form.
        
        Args:
            domain_diagram: The domain diagram to compile
            
        Returns:
            ExecutableDiagram with resolved connections and execution order
        """
        return self.diagram_compiler.compile(domain_diagram)
    
    def compile_with_validation(
        self, 
        domain_diagram: DomainDiagram
    ) -> tuple[Optional[ExecutableDiagram], list[str]]:
        """Compile a diagram with validation.
        
        Args:
            domain_diagram: The domain diagram to compile
            
        Returns:
            Tuple of (compiled diagram or None, list of error messages)
        """
        errors = []
        
        try:
            # Validate diagram structure first
            if not domain_diagram.nodes:
                errors.append("Diagram has no nodes")
                return None, errors
            
            # Check for start node
            start_nodes = [n for n in domain_diagram.nodes if n.node_type == "StartNode"]
            if not start_nodes:
                errors.append("Diagram must have at least one StartNode")
            elif len(start_nodes) > 1:
                errors.append("Diagram can only have one StartNode")
            
            # Check for endpoint node
            endpoint_nodes = [n for n in domain_diagram.nodes if n.node_type == "EndpointNode"]
            if not endpoint_nodes:
                errors.append("Diagram must have at least one EndpointNode")
            
            if errors:
                return None, errors
            
            # Attempt compilation
            compiled = self.diagram_compiler.compile(domain_diagram)
            return compiled, []
            
        except Exception as e:
            errors.append(f"Compilation failed: {str(e)}")
            return None, errors
    
    def validate_connections(self, domain_diagram: DomainDiagram) -> list[str]:
        """Validate connections in a diagram without compiling.
        
        Args:
            domain_diagram: The diagram to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Build node lookup
        node_ids = {node.id for node in domain_diagram.nodes}
        
        # Validate arrows
        for arrow in domain_diagram.arrows:
            if arrow.source_node_id not in node_ids:
                errors.append(f"Arrow references non-existent source node: {arrow.source_node_id}")
            if arrow.target_node_id not in node_ids:
                errors.append(f"Arrow references non-existent target node: {arrow.target_node_id}")
        
        return errors