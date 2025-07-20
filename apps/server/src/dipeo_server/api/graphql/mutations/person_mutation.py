"""GraphQL mutations for Person management - Auto-generated."""

import logging
import uuid
from typing import Optional
from datetime import datetime

import strawberry
from dipeo.models import Person
from dipeo.models import PersonID

from ..context import GraphQLContext
from ..generated_types import (
    CreatePersonInput,
    UpdatePersonInput,
    PersonResult,
    PersonID,
    DeleteResult,
    JSONScalar,
    MutationResult,
    PersonType,
)

logger = logging.getLogger(__name__)


@strawberry.type
class PersonMutations:
    """Handles Person CRUD operations."""
    
    @strawberry.mutation
    async def create_person(
        self,
        person_input: CreatePersonInput,
        info: strawberry.Info[GraphQLContext],
    ) -> PersonResult:
        """Create a new Person."""
        try:
            context: GraphQLContext = info.context
            person_service = context.get_service("person_service")
            
            # Extract fields from input
            data = {
                "label": getattr(person_input, "label", None),
                "llm_config": getattr(person_input, "llm_config", None),
                "diagram_id": getattr(person_input, "diagram_id", None),
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Validate required fields
            required_fields = ["label", "llm_config", "diagram_id"]
            missing = [f for f in required_fields if f not in data or data[f] is None]
            if missing:
                return PersonResult(
                    success=False,
                    error=f"Missing required fields: {', '.join(missing)}"
                )
            
            # Create the entity
            entity_id = f"person_{str(uuid.uuid4())[:8]}"
            
            # Build domain model
            person_data = Person(
                id=PersonID(entity_id),
                **data
            )
            
            # Save through service
            saved_entity = await person_service.create(person_data)
            

            
            return PersonResult(
                success=True,
                person=saved_entity,
                message=f"Person created successfully with ID: {entity_id}"
            )
            
        except ValueError as e:
            logger.error(f"Validation error creating Person: {e}")
            return PersonResult(
                success=False, 
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create Person: {e}", exc_info=True)
            return PersonResult(
                success=False, 
                error=f"Failed to create Person: {str(e)}"
            )

    @strawberry.mutation
    async def update_person(
        self,
        person_input: UpdatePersonInput,
        info: strawberry.Info[GraphQLContext],
    ) -> PersonResult:
        """Update an existing Person."""
        try:
            context: GraphQLContext = info.context
            service = context.get_service("person_service")
            
            # Get existing entity
            existing = await service.get(person_input.id)
            if not existing:
                return PersonResult(
                    success=False,
                    error=f"Person with ID {person_input.id} not found"
                )
            
            # Build updates
            updates = {}
            if person_input.label is not None:
                updates["label"] = person_input.label
            if person_input.llm_config is not None:
                updates["llm_config"] = person_input.llm_config
            
            if not updates:
                return PersonResult(
                    success=False,
                    error="No fields to update"
                )
            

            
            # Apply updates
            updated_entity = await person_service.update(person_input.id, updates)
            
            return PersonResult(
                success=True,
                person=updated_entity,
                message=f"Person updated successfully"
            )
            
        except ValueError as e:
            logger.error(f"Validation error updating Person: {e}")
            return PersonResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to update Person: {e}", exc_info=True)
            return PersonResult(
                success=False,
                error=f"Failed to update Person: {str(e)}"
            )

    @strawberry.mutation
    async def delete_person(
        self,
        person_id: PersonID,
        info: strawberry.Info[GraphQLContext],
    ) -> DeleteResult:
        """Delete a Person."""
        try:
            context: GraphQLContext = info.context
            person_service = context.get_service("person_service")
            
            # Check if exists
            existing = await person_service.get(person_id)
            if not existing:
                return DeleteResult(
                    success=False,
                    error=f"Person with ID {person_id} not found"
                )
            

            
            # Delete the entity
            await person_service.delete(person_id)
            
            return DeleteResult(
                success=True,
                deleted_id=str(person_id),
                message=f"Person deleted successfully"
            )
            
        except ValueError as e:
            logger.error(f"Validation error deleting Person: {e}")
            return DeleteResult(
                success=False,
                error=f"Cannot delete: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to delete Person: {e}", exc_info=True)
            return DeleteResult(
                success=False,
                error=f"Failed to delete Person: {str(e)}"
            )
