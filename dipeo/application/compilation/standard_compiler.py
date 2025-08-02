"""Standard diagram compiler that orchestrates domain compilation logic.

This compiler serves as the application-layer orchestrator, delegating
domain-specific transformations to the appropriate domain services.
"""

from typing import Any

from dipeo.core.compilation.diagram_compiler import DiagramCompiler
from dipeo.core.compilation.executable_diagram import ExecutableDiagram, ExecutableEdgeV2
from dipeo.diagram_generated import DomainDiagram, NodeID

from dipeo.domain.diagram.compilation import (
    NodeFactory,
    EdgeBuilder,
    ConnectionResolver,
)


class StandardCompiler(DiagramCompiler):
    """Application-layer compiler that orchestrates domain compilation.
    
    This compiler coordinates the compilation process using domain services:
    1. NodeFactory for creating typed nodes
    2. ConnectionResolver for resolving handle references
    3. EdgeBuilder for creating executable edges
    """
    
    def __init__(self):
        # Domain services for compilation
        self.node_factory = NodeFactory()
        self.connection_resolver = ConnectionResolver()
        self.edge_builder = EdgeBuilder()
        self.validation_errors: list[str] = []
    
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile domain diagram using domain services."""
        self.validation_errors.clear()
        
        # 1. Extract nodes and arrows as lists
        nodes_list = self._extract_nodes_list(domain_diagram)
        arrows_list = self._extract_arrows_list(domain_diagram)
        
        # 2. Create strongly-typed executable nodes using domain factory
        executable_nodes = self.node_factory.create_typed_nodes(nodes_list)
        self.validation_errors.extend(self.node_factory.get_validation_errors())
        node_map = {node.id: node for node in executable_nodes}
        
        # 3. Resolve handle references using domain resolver
        resolved_connections, resolution_errors = self.connection_resolver.resolve_connections(
            arrows_list, 
            nodes_list
        )
        self.validation_errors.extend(resolution_errors)
        
        # 4. Build executable edges using domain builder
        typed_edges, edge_errors = self.edge_builder.build_edges(
            arrows_list,
            resolved_connections,
            node_map
        )
        self.validation_errors.extend(edge_errors)
        
        # 5. Skip static execution order calculation (using dynamic ordering)
        # The engine will determine execution order dynamically at runtime
        
        # 6. Create immutable executable diagram
        return ExecutableDiagram(
            nodes=executable_nodes,
            edges=typed_edges,
            execution_order=None,  # No longer using static order
            metadata={
                "name": domain_diagram.metadata.name if domain_diagram.metadata else None,
                "validation_errors": self.validation_errors.copy()
            }
        )
    
    def _extract_nodes_list(self, domain_diagram: DomainDiagram) -> list:
        """Extract nodes as list from domain diagram."""
        if isinstance(domain_diagram.nodes, dict):
            return list(domain_diagram.nodes.values())
        return domain_diagram.nodes
    
    def _extract_arrows_list(self, domain_diagram: DomainDiagram) -> list:
        """Extract arrows as list from domain diagram."""
        if isinstance(domain_diagram.arrows, dict):
            return list(domain_diagram.arrows.values())
        return domain_diagram.arrows
    
    def decompile(self, executable_diagram: ExecutableDiagram) -> DomainDiagram:
        """Convert executable diagram back to domain representation."""
        from dipeo.diagram_generated.generated_nodes import PersonJobNode
        
        # Convert typed nodes back to domain nodes
        domain_nodes = []
        for node in executable_diagram.nodes:
            domain_node = {
                "id": node.id,
                "type": node.type.value if hasattr(node.type, 'value') else node.type,
                "position": {"x": node.position.x, "y": node.position.y},
                "data": node.to_dict()
            }
            domain_nodes.append(domain_node)
        
        # Convert edges back to arrows
        arrows = []
        for edge in executable_diagram.edges:
            arrow = {
                "id": edge.id,
                "source": edge.source_node_id,
                "target": edge.target_node_id,
                "sourceHandle": edge.source_output,
                "targetHandle": edge.target_input,
                "metadata": getattr(edge, 'metadata', {})
            }
            arrows.append(arrow)
        
        # Extract handles from nodes
        handles = []
        
        # Extract persons from PersonJobNodes
        persons = []
        for node in executable_diagram.nodes:
            if isinstance(node, PersonJobNode) and node.person_id:
                persons.append({
                    "id": node.person_id,
                    "name": node.person_id.capitalize()
                })
        
        return DomainDiagram(
            nodes=domain_nodes,
            arrows=arrows,
            handles=handles,
            persons=persons,
            metadata=executable_diagram.metadata
        )