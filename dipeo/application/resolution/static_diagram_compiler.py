"""Static diagram compiler implementation using strongly-typed nodes."""

from typing import Any

from dipeo.application.resolution.arrow_transformer import ArrowTransformer
from dipeo.application.resolution.compiler import NodeFactory
from dipeo.application.resolution.simple_order_calculator import SimpleOrderCalculator
from dipeo.application.resolution.handle_resolver import HandleResolver
from dipeo.core.static.diagram_compiler import DiagramCompiler
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableEdge
from dipeo.diagram_generated.generated_nodes import PersonJobNode
from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.domain.execution import NodeConnectionRules, DataTransformRules
from dipeo.diagram_generated import DomainDiagram, NodeID, NodeType


class ExecutableNodeImpl:
    """Compatibility wrapper for nodes used by ArrowTransformer.

    This provides a uniform interface for accessing node properties
    regardless of the underlying node implementation.
    """

    def __init__(
            self,
            id: NodeID,
            type: NodeType,
            position: Any,
            data: dict[str, Any]
    ):
        self.id = id
        self.type = type
        self.position = position
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "position": {
                "x": self.position.x,
                "y": self.position.y
            },
            "data": self.data
        }


class StaticDiagramCompiler(DiagramCompiler):
    """Compiles domain diagrams into strongly-typed executable diagrams."""
    
    def __init__(self):
        self.handle_resolver = HandleResolver()
        self.arrow_transformer = ArrowTransformer()
        self.order_calculator = SimpleOrderCalculator()
        self.node_factory = NodeFactory()
        self.connection_rules = NodeConnectionRules()
        self.transform_rules = DataTransformRules()
        self.validation_errors: list[str] = []
    
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile domain diagram with static type safety."""
        self.validation_errors.clear()
        
        # 1. Create strongly-typed executable nodes
        # Convert nodes dict to list if it's a map-based structure
        if isinstance(domain_diagram.nodes, dict):
            # Check what's in the nodes dict
            nodes_list = []
            for node_id, node_data in domain_diagram.nodes.items():
                # If node_data is a DomainNode object, use it directly
                # Otherwise, it might be a dict that needs to be converted
                if hasattr(node_data, 'type'):
                    nodes_list.append(node_data)
                else:
                    # This shouldn't happen with proper DomainDiagram
                    print(f"DEBUG: Unexpected node data type for {node_id}: {type(node_data)}")
                    print(f"DEBUG: Node data content: {node_data}")
            nodes_list = nodes_list
        else:
            nodes_list = domain_diagram.nodes
        executable_nodes = self.node_factory.create_typed_nodes(nodes_list)
        self.validation_errors.extend(self.node_factory.get_validation_errors())
        
        # 2. Resolve handles to connections
        # Convert arrows dict to list if it's a map-based structure
        arrows_list = list(domain_diagram.arrows.values()) if isinstance(domain_diagram.arrows, dict) else domain_diagram.arrows
        # Convert nodes to list if it's a map-based structure (same as we did for nodes_list above)
        nodes_for_resolver = list(domain_diagram.nodes.values()) if isinstance(domain_diagram.nodes, dict) else domain_diagram.nodes
        resolved_connections, handle_errors = self.handle_resolver.resolve_arrows(
            arrows_list,
            nodes_for_resolver
        )
        self.validation_errors.extend(handle_errors)
        
        # 3. Transform arrows to executable edges
        node_map = {node.id: node for node in executable_nodes}
        
        # Create ExecutableNodeImpl wrappers for compatibility with arrow transformer
        impl_nodes = [self._to_executable_impl(node) for node in executable_nodes]
        impl_map = {node.id: node for node in impl_nodes}
        
        edges, transform_errors = self.arrow_transformer.transform_arrows(
            arrows_list,  # Use the already converted arrows list
            resolved_connections,
            impl_map
        )
        self.validation_errors.extend(transform_errors)
        
        # Convert edges to typed ExecutableEdge
        typed_edges = self._create_typed_edges(edges, node_map)
        
        # 4. Calculate execution order
        execution_order, groups, order_errors = self.order_calculator.calculate_order(
            impl_nodes,
            edges
        )
        self.validation_errors.extend(order_errors)
        
        # 5. Create immutable executable diagram
        return ExecutableDiagram(
            nodes=executable_nodes,
            edges=typed_edges,
            execution_order=execution_order,
            metadata={
                "name": domain_diagram.metadata.name if domain_diagram.metadata else None,
                "execution_groups": [{
                    "level": group.level,
                    "nodes": list(group.nodes)
                } for group in groups] if groups else []
            }
        )
    
    
    def _to_executable_impl(self, node: ExecutableNode) -> ExecutableNodeImpl:
        """Convert typed node to ExecutableNodeImpl for compatibility."""
        return ExecutableNodeImpl(
            id=node.id,
            type=node.type,
            position=node.position,
            data=node.to_dict()
        )
    
    def _create_typed_edges(
        self, 
        edges: list[Any],
        node_map: dict[NodeID, ExecutableNode]
    ) -> list[ExecutableEdge]:
        """Convert edges to typed ExecutableEdge."""
        typed_edges = []
        
        for edge in edges:
            source_node = node_map.get(edge.source_node_id)
            target_node = node_map.get(edge.target_node_id)
            
            # Type-specific edge validation using domain rules
            if source_node and target_node:
                if not self.connection_rules.can_connect(source_node.type, target_node.type):
                    self.validation_errors.append(
                        f"Cannot connect {source_node.type} to {target_node.type}"
                    )
                    continue
            
            # Merge existing data_transform with node-type-based transforms
            existing_transform = edge.data_transform if hasattr(edge, 'data_transform') else {}
            type_based_transform = self.transform_rules.get_data_transform(source_node, target_node) if source_node and target_node else {}
            merged_transform = self.transform_rules.merge_transforms(existing_transform, type_based_transform)
            
            typed_edge = ExecutableEdge(
                id=edge.id,
                source_node_id=edge.source_node_id,
                target_node_id=edge.target_node_id,
                source_output=edge.source_output,
                target_input=edge.target_input,
                data_transform=merged_transform,
                metadata=edge.metadata if hasattr(edge, 'metadata') else {}
            )
            typed_edges.append(typed_edge)
        
        return typed_edges
    
    
    def decompile(self, executable_diagram: ExecutableDiagram) -> DomainDiagram:
        """Convert executable diagram back to domain representation."""
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
                "targetHandle": edge.target_input
            }
            arrows.append(arrow)
        
        # Extract handles from nodes - simplified for now
        handles = []
        
        # Extract persons from PersonJobNodes
        persons = []
        for node in executable_diagram.nodes:
            if isinstance(node, PersonJobNode) and node.person_id:
                # This is simplified - would need more complete person data
                persons.append({
                    "id": node.person_id,
                    "name": node.person_id.capitalize()
                })
        
        # Return domain diagram
        return DomainDiagram(
            nodes=domain_nodes,
            arrows=arrows,
            handles=handles,
            persons=persons,
            metadata=executable_diagram.metadata
        )


