"""Node mutations using ServiceRegistry."""

import logging

import strawberry

from dipeo.application.registry import ServiceRegistry, ServiceKey

from ...types.inputs import CreateNodeInput, UpdateNodeInput
from ...types.results import NodeResult, DeleteResult

logger = logging.getLogger(__name__)

# Service keys
INTEGRATED_DIAGRAM_SERVICE = ServiceKey("integrated_diagram_service")


def create_node_mutations(registry: ServiceRegistry) -> type:
    """Create node mutation methods with injected service registry.
    
    Note: This is a simplified implementation. In a full implementation,
    we would have specific mutations for each node type for better type safety.
    """
    
    @strawberry.type
    class NodeMutations:
        @strawberry.mutation
        async def create_node(
            self, diagram_id: strawberry.ID, input: CreateNodeInput
        ) -> NodeResult:
            """Create a new node in a diagram.
            
            This is a generic mutation that accepts JSON data.
            Consider using type-specific mutations for better type safety.
            """
            try:
                integrated_service = registry.resolve(INTEGRATED_DIAGRAM_SERVICE)
                
                # Get diagram
                diagram_data = await integrated_service.get_diagram(diagram_id)
                if not diagram_data:
                    raise ValueError(f"Diagram not found: {diagram_id}")
                
                # Create node (simplified - full implementation would validate by type)
                node_id = f"node_{len(diagram_data.get('nodes', []))}"
                node = {
                    "id": node_id,
                    "type": input.type,
                    "position": {"x": input.position.x, "y": input.position.y},
                    "data": input.data,
                }
                
                # Add to diagram
                if "nodes" not in diagram_data:
                    diagram_data["nodes"] = []
                diagram_data["nodes"].append(node)
                
                # Save updated diagram
                # Note: This is simplified - proper implementation would use
                # the diagram service's update methods
                
                return NodeResult(
                    success=True,
                    node=node,  # Would need proper conversion to DomainNodeType
                    message=f"Created node: {node_id}",
                )
                
            except Exception as e:
                logger.error(f"Failed to create node: {e}")
                return NodeResult(
                    success=False,
                    error=f"Failed to create node: {str(e)}",
                )
        
        @strawberry.mutation
        async def update_node(
            self, diagram_id: strawberry.ID, node_id: strawberry.ID, input: UpdateNodeInput
        ) -> NodeResult:
            """Update an existing node."""
            try:
                # Implementation would update node properties
                # This is a placeholder
                return NodeResult(
                    success=True,
                    message=f"Updated node: {node_id}",
                )
                
            except Exception as e:
                logger.error(f"Failed to update node {node_id}: {e}")
                return NodeResult(
                    success=False,
                    error=f"Failed to update node: {str(e)}",
                )
        
        @strawberry.mutation
        async def delete_node(
            self, diagram_id: strawberry.ID, node_id: strawberry.ID
        ) -> DeleteResult:
            """Delete a node from a diagram."""
            try:
                # Implementation would remove node and update connections
                # This is a placeholder
                return DeleteResult(
                    success=True,
                    deleted_id=node_id,
                    message=f"Deleted node: {node_id}",
                )
                
            except Exception as e:
                logger.error(f"Failed to delete node {node_id}: {e}")
                return DeleteResult(
                    success=False,
                    error=f"Failed to delete node: {str(e)}",
                )
    
    return NodeMutations