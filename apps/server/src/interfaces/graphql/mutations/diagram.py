"""Refactored diagram-related GraphQL mutations using Pydantic models."""
import strawberry
from typing import Optional
import logging
from datetime import datetime

from ..types.results import DiagramResult, DeleteResult
from ..types.scalars import DiagramID, JSONScalar as JSON
from ..types.inputs import CreateDiagramInput
from ..types.enums import DiagramFormat
from ..context import GraphQLContext
from src.domains.diagram.models import DiagramMetadata, DomainDiagram, DiagramDictFormat
from src.domains.diagram.converters import diagram_dict_to_graphql
from ..models.input_models import (
    CreateDiagramInput as PydanticCreateDiagramInput
)

logger = logging.getLogger(__name__)


@strawberry.type
class DiagramMutations:
    """Mutations for diagram operations."""
    
    @strawberry.mutation
    async def create_diagram(self, input: CreateDiagramInput, info) -> DiagramResult:
        """Create a new diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticCreateDiagramInput(
                name=input.name,
                description=input.description,
                author=input.author,
                tags=input.tags
            )
            
            # Create diagram metadata using validated Pydantic data
            metadata = DiagramMetadata(
                name=pydantic_input.name,  # Already trimmed by validation
                description=pydantic_input.description or "",
                author=pydantic_input.author or "",
                tags=pydantic_input.tags,  # Already cleaned of duplicates
                created=datetime.now(),
                modified=datetime.now()
            )
            
            # Create empty diagram structure using Pydantic model
            diagram_model = DomainDiagram(
                nodes=[],
                arrows=[],
                handles=[],
                persons=[],
                api_keys=[],
                metadata=metadata
            )
            
            # Convert to dict for service
            diagram_data = diagram_model.model_dump()
            
            # Create the diagram file
            path = diagram_service.create_diagram(pydantic_input.name, diagram_data)
            
            # Convert to GraphQL format
            # diagram_model is already a DomainDiagram with lists, not dicts
            graphql_diagram = diagram_model
            
            return DiagramResult(
                success=True,
                diagram=graphql_diagram,
                message=f"Created diagram at {path}"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error creating diagram: {e}")
            return DiagramResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create diagram: {e}")
            return DiagramResult(
                success=False,
                error=f"Failed to create diagram: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_diagram(self, id: DiagramID, info) -> DeleteResult:
        """Delete a diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # DiagramID is the path to the diagram file
            diagram_service.delete_diagram(id)
            
            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted diagram: {id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete diagram {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete diagram: {str(e)}"
            )
    
