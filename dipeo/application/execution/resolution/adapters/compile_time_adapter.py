"""Adapter to make new compile-time interfaces work with existing compiler.

This adapter bridges the gap between the new CompileTimeResolver interface
and the existing StaticDiagramCompiler implementation.
"""

from typing import Any

from dipeo.diagram_generated import DomainArrow, DomainNode, NodeID
from dipeo.core.static.executable_diagram import ExecutableNode, ExecutableEdge
from dipeo.domain.execution import NodeConnectionRules, DataTransformRules

from ..interfaces import (
    CompileTimeResolver,
    Connection,
    TransformRules,
)
from ....resolution.handle_resolver import HandleResolver
from ....resolution.arrow_transformer import ArrowTransformer


class CompileTimeResolverAdapter(CompileTimeResolver):
    """Adapts existing resolution components to the new interface."""
    
    def __init__(self):
        self.handle_resolver = HandleResolver()
        self.arrow_transformer = ArrowTransformer()
        self.connection_rules = NodeConnectionRules()
        self.transform_rules = DataTransformRules()
    
    def resolve_connections(
        self, 
        arrows: list[DomainArrow], 
        nodes: list[DomainNode]
    ) -> list[Connection]:
        """Use existing handle resolver and convert to Connection objects."""
        # Use existing handle resolver
        resolved_connections, errors = self.handle_resolver.resolve_arrows(arrows, nodes)
        
        # Convert to Connection objects
        connections = []
        for conn in resolved_connections:
            connection = Connection(
                source_node_id=conn['source_node_id'],
                target_node_id=conn['target_node_id'], 
                source_output=conn.get('source_output'),
                target_input=conn.get('target_input'),
                metadata=conn.get('metadata', {})
            )
            connections.append(connection)
        
        return connections
    
    def determine_transformation_rules(
        self, 
        connection: Connection,
        source_node: ExecutableNode,
        target_node: ExecutableNode
    ) -> TransformRules:
        """Determine transformation rules using existing logic."""
        # Get type-based transforms
        type_based_transform = self.transform_rules.get_data_transform(
            source_node, 
            target_node
        )
        
        # Extract any arrow-specific transforms from metadata
        arrow_transform = connection.metadata.get('data_transform', {})
        
        # Merge transforms
        merged = self.transform_rules.merge_transforms(
            arrow_transform,
            type_based_transform
        )
        
        # Wrap in TransformRules object
        return TransformRules(merged)
    
    def validate_connection(
        self,
        source_node: ExecutableNode,
        target_node: ExecutableNode
    ) -> tuple[bool, str | None]:
        """Validate connection using existing rules."""
        can_connect = self.connection_rules.can_connect(
            source_node.type,
            target_node.type
        )
        
        if not can_connect:
            error = f"Cannot connect {source_node.type} to {target_node.type}"
            return False, error
        
        return True, None


class ExecutableNodeAdapter:
    """Adapts between different node representations."""
    
    @staticmethod
    def to_executable_impl(node: ExecutableNode) -> Any:
        """Convert typed node to ExecutableNodeImpl for compatibility."""
        # Import here to avoid circular dependency
        from ..static_diagram_compiler import ExecutableNodeImpl
        
        return ExecutableNodeImpl(
            id=node.id,
            type=node.type,
            position=node.position,
            data=node.to_dict()
        )
    
    @staticmethod 
    def from_domain_node(domain_node: DomainNode) -> dict[str, Any]:
        """Convert domain node to dict representation."""
        return {
            "id": domain_node.id,
            "type": domain_node.type,
            "position": domain_node.position,
            "data": domain_node.data or {}
        }


class EdgeAdapter:
    """Adapts between ExecutableEdge representations."""
    
    @staticmethod
    def create_executable_edge(
        edge_data: dict[str, Any],
        transform_rules: TransformRules | None = None
    ) -> ExecutableEdge:
        """Create ExecutableEdge from edge data and rules."""
        data_transform = transform_rules.rules if transform_rules else {}
        
        # Merge with existing data_transform if present
        if 'data_transform' in edge_data:
            data_transform = {**edge_data['data_transform'], **data_transform}
        
        return ExecutableEdge(
            id=edge_data['id'],
            source_node_id=edge_data['source_node_id'],
            target_node_id=edge_data['target_node_id'],
            source_output=edge_data.get('source_output'),
            target_input=edge_data.get('target_input'),
            data_transform=data_transform,
            metadata=edge_data.get('metadata', {})
        )
    
    @staticmethod
    def to_enhanced_edge(edge: ExecutableEdge) -> Any:
        """Convert to enhanced edge representation if needed."""
        # For now, just return the edge as-is
        # In future, could convert to ExecutableEdgeV2
        return edge