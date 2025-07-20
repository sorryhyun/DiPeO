"""GraphQL mutations for Diagram management - Auto-generated."""

import logging
import uuid
from typing import Optional
from datetime import datetime

import strawberry
from dipeo.models import Diagram
from dipeo.models import DiagramID

from ..context import GraphQLContext
from ..generated_types import (
    CreateDiagramInput,
    UpdateDiagramInput,
    DiagramResult,
    DiagramID,
    DeleteResult,
    JSONScalar,
    MutationResult,
    DiagramType,
)

logger = logging.getLogger(__name__)


@strawberry.type
class DiagramMutations:
    """Handles Diagram CRUD operations."""
    
    @strawberry.mutation
    async def create_diagram(
        self,
        diagram_input: CreateDiagramInput,
        info: strawberry.Info[GraphQLContext],
    ) -> DiagramResult:
        """Create a new Diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.get_service("diagram_service")
            
            # Extract fields from input
            data = {
                "name": getattr(diagram_input, "name", None),
                "description": getattr(diagram_input, "description", None),
                "author": getattr(diagram_input, "author", None),
                "tags": getattr(diagram_input, "tags", None),
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Validate required fields
            required_fields = ["name"]
            missing = [f for f in required_fields if f not in data or data[f] is None]
            if missing:
                return DiagramResult(
                    success=False,
                    error=f"Missing required fields: {', '.join(missing)}"
                )
            
            # Create the entity
            entity_id = f"diagram_{str(uuid.uuid4())[:8]}"
            
            # Build domain model
            diagram_data = Diagram(
                id=DiagramID(entity_id),
                **data
            )
            
            # Save through service
            saved_entity = await diagram_service.create(diagram_data)
            

            
            return DiagramResult(
                success=True,
                diagram=saved_entity,
                message=f"Diagram created successfully with ID: {entity_id}"
            )
            
        except ValueError as e:
            logger.error(f"Validation error creating Diagram: {e}")
            return DiagramResult(
                success=False, 
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create Diagram: {e}", exc_info=True)
            return DiagramResult(
                success=False, 
                error=f"Failed to create Diagram: {str(e)}"
            )

    @strawberry.mutation
    async def update_diagram(
        self,
        diagram_input: UpdateDiagramInput,
        info: strawberry.Info[GraphQLContext],
    ) -> DiagramResult:
        """Update an existing Diagram."""
        try:
            context: GraphQLContext = info.context
            service = context.get_service("diagram_service")
            
            # Get existing entity
            existing = await service.get(diagram_input.id)
            if not existing:
                return DiagramResult(
                    success=False,
                    error=f"Diagram with ID {diagram_input.id} not found"
                )
            
            # Build updates
            updates = {}
            if diagram_input.name is not None:
                updates["name"] = diagram_input.name
            if diagram_input.description is not None:
                updates["description"] = diagram_input.description
            if diagram_input.author is not None:
                updates["author"] = diagram_input.author
            if diagram_input.tags is not None:
                updates["tags"] = diagram_input.tags
            
            if not updates:
                return DiagramResult(
                    success=False,
                    error="No fields to update"
                )
            

            
            # Apply updates
            updated_entity = await diagram_service.update(diagram_input.id, updates)
            
            return DiagramResult(
                success=True,
                diagram=updated_entity,
                message=f"Diagram updated successfully"
            )
            
        except ValueError as e:
            logger.error(f"Validation error updating Diagram: {e}")
            return DiagramResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to update Diagram: {e}", exc_info=True)
            return DiagramResult(
                success=False,
                error=f"Failed to update Diagram: {str(e)}"
            )

    @strawberry.mutation
    async def delete_diagram(
        self,
        diagram_id: DiagramID,
        info: strawberry.Info[GraphQLContext],
    ) -> DeleteResult:
        """Delete a Diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.get_service("diagram_service")
            
            # Check if exists
            existing = await diagram_service.get(diagram_id)
            if not existing:
                return DeleteResult(
                    success=False,
                    error=f"Diagram with ID {diagram_id} not found"
                )
            

            
            # Delete the entity
            await diagram_service.delete(diagram_id)
            
            return DeleteResult(
                success=True,
                deleted_id=str(diagram_id),
                message=f"Diagram deleted successfully"
            )
            
        except ValueError as e:
            logger.error(f"Validation error deleting Diagram: {e}")
            return DeleteResult(
                success=False,
                error=f"Cannot delete: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to delete Diagram: {e}", exc_info=True)
            return DeleteResult(
                success=False,
                error=f"Failed to delete Diagram: {str(e)}"
            )
