"""Interface-based diagram compiler implementation.

This replaces StaticDiagramCompiler with an implementation that uses
the new interfaces for better separation of concerns.
"""

from typing import Any

from dipeo.core.execution.diagram_compiler import DiagramCompiler
from dipeo.core.execution.executable_diagram import ExecutableDiagram, ExecutableEdge
from dipeo.diagram_generated import DomainDiagram, NodeID, NodeType
from dipeo.core.execution.executable_diagram import ExecutableNode

from dipeo.application.execution.resolution.interfaces import (
    CompileTimeResolver,
    Connection,
    TransformRules,
    ExecutableEdgeV2,
)
from dipeo.application.execution.resolution.adapters import (
    CompileTimeResolverAdapter,
    EdgeAdapter,
)
from dipeo.application.resolution.compiler import NodeFactory
from dipeo.application.resolution.simple_order_calculator import SimpleOrderCalculator


class InterfaceBasedDiagramCompiler(DiagramCompiler):
    """Compiles domain diagrams using the new interface-based approach.
    
    This compiler uses clear separation between compile-time and runtime
    concerns through well-defined interfaces.
    """
    
    def __init__(self, compile_time_resolver: CompileTimeResolver | None = None):
        # Use adapter for backward compatibility if no resolver provided
        self.compile_time_resolver = compile_time_resolver or CompileTimeResolverAdapter()
        self.node_factory = NodeFactory()
        self.order_calculator = SimpleOrderCalculator()
        self.edge_adapter = EdgeAdapter()
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
        # Create compatibility nodes for order calculator
        impl_nodes = [self._to_impl_node(node) for node in executable_nodes]
        
        # Convert typed edges for order calculator
        order_edges = [self._to_order_edge(edge) for edge in typed_edges]
        
        execution_order, groups, order_errors = self.order_calculator.calculate_order(
            impl_nodes,
            order_edges
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
    ) -> list[ExecutableEdge]:
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
            
            # Create edge data structure
            edge_metadata = {**conn.metadata, **arrow_metadata}
            if arrow_label:
                edge_metadata['label'] = arrow_label
                
            edge_data = {
                'id': arrow_id or f"{conn.source_node_id}->{conn.target_node_id}",
                'source_node_id': conn.source_node_id,
                'target_node_id': conn.target_node_id,
                'source_output': conn.source_output,
                'target_input': conn.target_input,
                'metadata': edge_metadata
            }
            
            # Create ExecutableEdge using adapter
            typed_edge = self.edge_adapter.create_executable_edge(
                edge_data,
                transform_rules
            )
            typed_edges.append(typed_edge)
        
        return typed_edges
    
    def _to_impl_node(self, node: ExecutableNode) -> Any:
        """Convert node for order calculator compatibility."""
        # Import here to avoid circular dependency
        from .static_diagram_compiler import ExecutableNodeImpl
        
        return ExecutableNodeImpl(
            id=node.id,
            type=node.type,
            position=node.position,
            data=node.to_dict()
        )
    
    def _to_order_edge(self, edge: ExecutableEdge) -> Any:
        """Convert edge for order calculator compatibility."""
        # Create simple edge structure for order calculation
        class SimpleEdge:
            def __init__(self, source_node_id, target_node_id):
                self.source_node_id = source_node_id
                self.target_node_id = target_node_id
        
        return SimpleEdge(edge.source_node_id, edge.target_node_id)
    
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