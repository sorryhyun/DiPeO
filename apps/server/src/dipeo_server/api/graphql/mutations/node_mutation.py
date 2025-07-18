"""GraphQL mutations for Node management - Auto-generated."""

import logging
import uuid
from typing import Optional
from datetime import datetime

import strawberry
from dipeo.models import Node
from dipeo.models import NodeID

from ..context import GraphQLContext
from ..generated_types import (
    CreateNodeInput,
    UpdateNodeInput,
    NodeResult,
    NodeID,
    DeleteResult,
    JSONScalar,
    MutationResult,
    NodeType,
)

logger = logging.getLogger(__name__)


@strawberry.type
class NodeMutations:
    """Handles Node CRUD operations."""
    
    @strawberry.mutation
    async def create_node(
        self,
        node_input: CreateNodeInput,
        info: strawberry.Info[GraphQLContext],
    ) -> NodeResult:
        """Create a new Node."""
        try:
            context: GraphQLContext = info.context
            node_service = context.get_service("node_service")
            
            # Extract fields from input
            data = {
                "type": getattr(node_input, "type", None),
                "position": getattr(node_input, "position", None),
                "data": getattr(node_input, "data", None),
                "diagram_id": getattr(node_input, "diagram_id", None),
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Validate required fields
            required_fields = ["type", "position", "data", "diagram_id"]
            missing = [f for f in required_fields if f not in data or data[f] is None]
            if missing:
                return NodeResult(
                    success=False,
                    error=f"Missing required fields: {', '.join(missing)}"
                )
            
            # Create the entity
            entity_id = f"node_{str(uuid.uuid4())[:8]}"
            
            # Build domain model
            node_data = Node(
                id=NodeID(entity_id),
                **data
            )
            
            # Save through service
            saved_entity = await node_service.create(node_data)
            

            
            return NodeResult(
                success=True,
                node=saved_entity,
                message=f"Node created successfully with ID: {entity_id}"
            )
            
        except ValueError as e:
            logger.error(f"Validation error creating Node: {e}")
            return NodeResult(
                success=False, 
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create Node: {e}", exc_info=True)
            return NodeResult(
                success=False, 
                error=f"Failed to create Node: {str(e)}"
            )

    @strawberry.mutation
    async def update_node(
        self,
        node_input: UpdateNodeInput,
        info: strawberry.Info[GraphQLContext],
    ) -> NodeResult:
        """Update an existing Node."""
        try:
            context: GraphQLContext = info.context
            service = context.get_service("node_service")
            
            # Get existing entity
            existing = await service.get(node_input.id)
            if not existing:
                return NodeResult(
                    success=False,
                    error=f"Node with ID {node_input.id} not found"
                )
            
            # Build updates
            updates = {}
            if node_input.type is not None:
                updates["type"] = node_input.type
            if node_input.position is not None:
                updates["position"] = node_input.position
            if node_input.data is not None:
                updates["data"] = node_input.data
            
            if not updates:
                return NodeResult(
                    success=False,
                    error="No fields to update"
                )
            

            
            # Apply updates
            updated_entity = await node_service.update(node_input.id, updates)
            
            return NodeResult(
                success=True,
                node=updated_entity,
                message=f"Node updated successfully"
            )
            
        except ValueError as e:
            logger.error(f"Validation error updating Node: {e}")
            return NodeResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to update Node: {e}", exc_info=True)
            return NodeResult(
                success=False,
                error=f"Failed to update Node: {str(e)}"
            )

    @strawberry.mutation
    async def delete_node(
        self,
        node_id: NodeID,
        info: strawberry.Info[GraphQLContext],
    ) -> DeleteResult:
        """Delete a Node."""
        try:
            context: GraphQLContext = info.context
            node_service = context.get_service("node_service")
            
            # Check if exists
            existing = await node_service.get(node_id)
            if not existing:
                return DeleteResult(
                    success=False,
                    error=f"Node with ID {node_id} not found"
                )
            

            
            # Delete the entity
            await node_service.delete(node_id)
            
            return DeleteResult(
                success=True,
                deleted_id=str(node_id),
                message=f"Node deleted successfully"
            )
            
        except ValueError as e:
            logger.error(f"Validation error deleting Node: {e}")
            return DeleteResult(
                success=False,
                error=f"Cannot delete: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to delete Node: {e}", exc_info=True)
            return DeleteResult(
                success=False,
                error=f"Failed to delete Node: {str(e)}"
            )
