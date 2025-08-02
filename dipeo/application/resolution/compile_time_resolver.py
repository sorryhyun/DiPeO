"""Direct implementation of CompileTimeResolver for diagram compilation.

This resolver handles static analysis during diagram compilation, including
connection resolution and transformation rule determination.
"""

from dipeo.diagram_generated import DomainArrow, DomainNode
from dipeo.diagram_generated.enums import NodeType
from dipeo.application.resolution.input_resolution import (
    Connection,
    TransformRules,
)
from dipeo.core.compilation.executable_diagram import ExecutableNode
from dipeo.domain.execution import NodeConnectionRules, DataTransformRules

from dipeo.domain.diagram.compilation import ConnectionResolver, EdgeBuilder


class StandardCompileTimeResolver:
    """Standard implementation of compile-time resolution.
    
    This resolver combines handle resolution, arrow transformation, and
    rule determination into a cohesive compile-time analysis phase.
    """
    
    def __init__(self):
        self.connection_resolver = ConnectionResolver()
        self.edge_builder = EdgeBuilder()
        self.connection_rules = NodeConnectionRules()
        self.transform_rules = DataTransformRules()
    
    def resolve_connections(
        self, 
        arrows: list[DomainArrow], 
        nodes: list[DomainNode]
    ) -> list[Connection]:
        """Resolve arrows to concrete connections between nodes.
        
        This involves:
        1. Resolving handle references to actual node connections
        2. Converting resolved arrows to Connection objects
        3. Preserving arrow metadata for later use
        """
        # Resolve handle references
        resolved_connections, errors = self.connection_resolver.resolve_connections(arrows, nodes)
        
        # Convert to Connection objects
        connections = []
        for conn in resolved_connections:
            connection = Connection(
                source_node_id=conn.source_node_id,
                target_node_id=conn.target_node_id,
                source_output=str(conn.source_handle_label) if conn.source_handle_label else None,
                target_input=str(conn.target_handle_label) if conn.target_handle_label else None,
                metadata={'arrow_id': conn.arrow_id}
            )
            connections.append(connection)
        
        return connections
    
    def determine_transformation_rules(
        self, 
        connection: Connection,
        source_node: ExecutableNode,
        target_node: ExecutableNode
    ) -> TransformRules:
        """Determine all transformation rules for a connection.
        
        This combines:
        1. Type-based transformations (e.g., PersonJob -> string extraction)
        2. Arrow-specific transformations from metadata
        3. Any custom rules based on node configurations
        """
        # Get type-based transforms
        type_based_transform = self.transform_rules.get_data_transform(
            source_node.type,
            target_node.type
        )
        
        # Extract any arrow-specific transforms from metadata
        arrow_transform = connection.metadata.get('data_transform', {})
        
        # Merge transforms (arrow-specific takes precedence)
        merged = self.transform_rules.merge_transforms(
            arrow_transform,
            type_based_transform
        )
        
        # Check for special cases (e.g., condition nodes)
        if target_node.type == NodeType.CONDITION:
            # Add branch_on_condition transformation
            merged['branch_on_condition'] = True
        
        # Wrap in TransformRules object
        return TransformRules(merged)
    
    def validate_connection(
        self,
        source_node: ExecutableNode,
        target_node: ExecutableNode
    ) -> tuple[bool, str | None]:
        """Validate if a connection between two nodes is allowed.
        
        Uses the domain's connection rules to determine validity.
        """
        can_connect = self.connection_rules.can_connect(
            source_node.type,
            target_node.type
        )
        
        if not can_connect:
            error = f"Cannot connect {source_node.type.value} to {target_node.type.value}"
            return False, error
        
        return True, None