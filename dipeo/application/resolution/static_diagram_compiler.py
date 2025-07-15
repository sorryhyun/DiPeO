"""Static diagram compiler implementation using strongly-typed nodes."""

from typing import Any

from dipeo.application.resolution.arrow_transformer import ArrowTransformer, ExecutableNodeImpl
from dipeo.application.resolution.simple_order_calculator import SimpleOrderCalculator
from dipeo.application.resolution.handle_resolver import HandleResolver
from dipeo.core.static.diagram_compiler import DiagramCompiler
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableEdge
from dipeo.core.static.generated_nodes import (
    ApiJobNode,
    CodeJobNode,
    ConditionNode,
    EndpointNode,
    ExecutableNode,
    PersonJobNode,
    StartNode,
    create_executable_node,
)
from dipeo.models import DomainDiagram, NodeID


class StaticDiagramCompiler(DiagramCompiler):
    """Compiles domain diagrams into strongly-typed executable diagrams."""
    
    def __init__(self):
        self.handle_resolver = HandleResolver()
        self.arrow_transformer = ArrowTransformer()
        self.order_calculator = SimpleOrderCalculator()
        self.validation_errors: list[str] = []
    
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile domain diagram with static type safety."""
        self.validation_errors.clear()
        
        # 1. Create strongly-typed executable nodes
        executable_nodes = self._create_typed_nodes(domain_diagram.nodes)
        
        # 2. Resolve handles to connections
        resolved_connections, handle_errors = self.handle_resolver.resolve_arrows(
            domain_diagram.arrows,
            domain_diagram.nodes
        )
        self.validation_errors.extend(handle_errors)
        
        # 3. Transform arrows to executable edges
        node_map = {node.id: node for node in executable_nodes}
        
        # Create ExecutableNodeImpl wrappers for compatibility with arrow transformer
        impl_nodes = [self._to_executable_impl(node) for node in executable_nodes]
        impl_map = {node.id: node for node in impl_nodes}
        
        edges, transform_errors = self.arrow_transformer.transform_arrows(
            domain_diagram.arrows,
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
    
    def _create_typed_nodes(self, domain_nodes) -> list[ExecutableNode]:
        """Create strongly-typed nodes with compile-time validation."""
        typed_nodes = []
        
        for node in domain_nodes:
            try:
                # Factory creates the appropriate immutable node type
                typed_node = create_executable_node(
                    node_type=node.type,
                    node_id=node.id,
                    position=node.position,
                    label=node.data.get("label", "") if node.data else "",
                    data=node.data or {}
                )
                
                # Additional type-specific validation
                self._validate_typed_node(typed_node)
                typed_nodes.append(typed_node)
                
            except (ValueError, TypeError) as e:
                self.validation_errors.append(
                    f"Failed to create {node.type} node {node.id}: {e}"
                )
        
        return typed_nodes
    
    def _validate_typed_node(self, node: ExecutableNode) -> None:
        """Type-specific validation using actual node types."""
        if isinstance(node, PersonJobNode):
            if not node.person_id and not node.llm_config:
                self.validation_errors.append(
                    f"Person node {node.id} must have either person_id or llm_config"
                )
            if node.max_iteration < 1:
                self.validation_errors.append(
                    f"Person node {node.id} max_iteration must be >= 1"
                )
                
        elif isinstance(node, ConditionNode):
            if not node.expression and node.condition_type == "expression":
                self.validation_errors.append(
                    f"Condition node {node.id} with type 'expression' must have expression"
                )
                
        elif isinstance(node, StartNode):
            if node.trigger_mode and not node.hook_event:
                self.validation_errors.append(
                    f"Start node {node.id} with trigger_mode must have hook_event"
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
            
            # Type-specific edge validation
            if source_node and target_node:
                if not self._can_connect(source_node, target_node):
                    self.validation_errors.append(
                        f"Cannot connect {source_node.type} to {target_node.type}"
                    )
                    continue
            
            # Merge existing data_transform with node-type-based transforms
            existing_transform = edge.data_transform if hasattr(edge, 'data_transform') else {}
            type_based_transform = self._get_data_transform(source_node, target_node) if source_node and target_node else {}
            merged_transform = {**existing_transform, **type_based_transform}
            
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
    
    def _can_connect(self, source: ExecutableNode, target: ExecutableNode) -> bool:
        """Type-safe connection validation."""
        # Use actual node types for validation
        if isinstance(target, StartNode):
            return False  # Start nodes cannot have inputs
        
        if isinstance(source, EndpointNode):
            return False  # Endpoint nodes cannot have outputs
        
        if isinstance(source, (PersonJobNode, ConditionNode, CodeJobNode, ApiJobNode)):
            # These can connect to most node types
            return not isinstance(target, StartNode)
        
        return True  # Default allow
    
    def _get_data_transform(
        self, 
        source: ExecutableNode, 
        target: ExecutableNode
    ) -> dict[str, Any]:
        """Define data transformations based on node types."""
        transforms = {}
        
        # Example: Person node output transformation
        if isinstance(source, PersonJobNode) and source.tools:
            transforms["extract_tool_results"] = True
        
        # Example: Condition node branching
        if isinstance(source, ConditionNode):
            transforms["branch_on"] = "condition_result"
        
        return transforms
    
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


