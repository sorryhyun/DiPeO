"""Interface-based diagram compiler implementation.

This replaces StaticDiagramCompiler with an implementation that uses
the new interfaces for better separation of concerns.
"""

from typing import Any

from dipeo.core.compilation.diagram_compiler import DiagramCompiler
from dipeo.core.compilation.executable_diagram import ExecutableDiagram, ExecutableEdgeV2, ExecutableNode
from dipeo.diagram_generated import DomainDiagram, NodeID, NodeType

from dipeo.application.resolution.input_resolution import (
    CompileTimeResolver,
    Connection,
    TransformRules,
)
from dipeo.application.resolution.compile_time_resolver import StandardCompileTimeResolver
from dipeo.domain.diagram.compilation import NodeFactory
from dipeo.application.resolution.simple_order_calculator import SimpleOrderCalculator


class InterfaceBasedDiagramCompiler(DiagramCompiler):
    """Compiles domain diagrams using the new interface-based approach.
    
    This compiler uses clear separation between compile-time and runtime
    concerns through well-defined interfaces.
    """
    
    def __init__(self, compile_time_resolver: CompileTimeResolver | None = None):
        # Use standard resolver if none provided
        self.compile_time_resolver = compile_time_resolver or StandardCompileTimeResolver()
        self.node_factory = NodeFactory()
        self.order_calculator = SimpleOrderCalculator()
        self.validation_errors: list[str] = []
    
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile domain diagram with interface-based approach."""
        self.validation_errors.clear()
        
        # 1. Convert domain nodes to list format
        nodes_list = self._extract_nodes_list(domain_diagram)
        arrows_list = self._extract_arrows_list(domain_diagram)
        
        # 2. Create strongly-typed executable nodes
        executable_nodes = self.node_factory.create_typed_nodes(nodes_list)
        self.validation_errors.extend(self.node_factory.get_validation_errors())
        node_map = {node.id: node for node in executable_nodes}
        
        # 3. Resolve connections using interface
        connections = self.compile_time_resolver.resolve_connections(
            arrows_list, 
            nodes_list
        )
        
        # 4. Create executable edges with transformation rules
        typed_edges = self._create_enhanced_edges(
            connections,
            arrows_list, 
            node_map
        )
        
        # 5. Calculate execution order
        execution_order, groups, order_errors = self.order_calculator.calculate_order(
            executable_nodes,
            typed_edges
        )
        self.validation_errors.extend(order_errors)
        
        # 6. Create immutable executable diagram
        return ExecutableDiagram(
            nodes=executable_nodes,
            edges=typed_edges,
            execution_order=execution_order,
            metadata={
                "name": domain_diagram.metadata.name if domain_diagram.metadata else None,
                "execution_groups": [{
                    "level": group.level,
                    "nodes": list(group.nodes)
                } for group in groups] if groups else [],
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
    
    def _create_enhanced_edges(
        self,
        connections: list[Connection],
        arrows: list[Any],
        node_map: dict[NodeID, ExecutableNode]
    ) -> list[ExecutableEdgeV2]:
        """Create executable edges with enhanced transformation rules."""
        typed_edges = []
        
        # Create arrow lookup by ID for metadata
        arrow_map = {arrow.id: arrow for arrow in arrows if hasattr(arrow, 'id')}
        
        for conn in connections:
            source_node = node_map.get(conn.source_node_id)
            target_node = node_map.get(conn.target_node_id)
            
            if not source_node or not target_node:
                self.validation_errors.append(
                    f"Missing node for connection: {conn.source_node_id} -> {conn.target_node_id}"
                )
                continue
            
            # Validate connection
            is_valid, error_msg = self.compile_time_resolver.validate_connection(
                source_node, target_node
            )
            if not is_valid:
                self.validation_errors.append(error_msg)
                continue
            
            # Determine transformation rules
            transform_rules = self.compile_time_resolver.determine_transformation_rules(
                conn, source_node, target_node
            )
            
            # Find original arrow for ID and additional metadata
            arrow_id = conn.metadata.get('arrow_id')  # From CompileTimeResolverAdapter
            arrow_metadata = {}
            arrow_label = None
            
            # Find the arrow by ID to get its metadata and label
            if arrow_id and arrow_id in arrow_map:
                arrow = arrow_map[arrow_id]
                arrow_metadata = getattr(arrow, 'metadata', {})
                arrow_label = getattr(arrow, 'label', None)
            
            # Create edge metadata
            edge_metadata = {**conn.metadata, **arrow_metadata}
            if arrow_label:
                edge_metadata['label'] = arrow_label
            
            # Extract transform rules
            transform_rules_dict = transform_rules.rules if transform_rules else {}
            
            # Create ExecutableEdge directly
            typed_edge = ExecutableEdgeV2(
                id=arrow_id or f"{conn.source_node_id}->{conn.target_node_id}",
                source_node_id=conn.source_node_id,
                target_node_id=conn.target_node_id,
                source_output=conn.source_output or 'default',
                target_input=conn.target_input or 'default',
                transform_rules=transform_rules_dict,
                metadata=edge_metadata
            )
            typed_edges.append(typed_edge)
        
        return typed_edges
    
    
    def decompile(self, executable_diagram: ExecutableDiagram) -> DomainDiagram:
        """Convert executable diagram back to domain representation."""
        # This is mostly unchanged from the original implementation
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