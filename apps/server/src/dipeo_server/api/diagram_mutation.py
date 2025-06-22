"""GraphQL mutations for diagram management."""

import logging
from datetime import datetime

import strawberry

from dipeo_server.domains.diagram.models import (
    DiagramMetadata,
    DomainDiagram,
)

from .context import GraphQLContext
from .inputs_types import CreateDiagramInput
from .models.input_models import CreateDiagramInput as PydanticCreateDiagramInput
from .results_types import DeleteResult, DiagramResult
from .scalars_types import DiagramID

logger = logging.getLogger(__name__)


@strawberry.type
class DiagramMutations:
    """Handles diagram CRUD operations."""

    @strawberry.mutation
    async def create_diagram(self, input: CreateDiagramInput, info) -> DiagramResult:
        """Creates new empty diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service

            pydantic_input = PydanticCreateDiagramInput(
                name=input.name,
                description=input.description,
                author=input.author,
                tags=input.tags,
            )

            metadata = DiagramMetadata(
                name=pydantic_input.name,
                description=pydantic_input.description or "",
                author=pydantic_input.author or "",
                tags=pydantic_input.tags,
                created=datetime.now(),
                modified=datetime.now(),
            )

            diagram_model = DomainDiagram(
                nodes=[],
                arrows=[],
                handles=[],
                persons=[],
                api_keys=[],
                metadata=metadata,
            )

            diagram_data = diagram_model.model_dump()

            path = diagram_service.create_diagram(pydantic_input.name, diagram_data)

            graphql_diagram = diagram_model

            return DiagramResult(
                success=True,
                diagram=graphql_diagram,
                message=f"Created diagram at {path}",
            )

        except ValueError as e:
            logger.error(f"Validation error creating diagram: {e}")
            return DiagramResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to create diagram: {e}")
            return DiagramResult(
                success=False, error=f"Failed to create diagram: {e!s}"
            )

    @strawberry.mutation
    async def delete_diagram(self, id: DiagramID, info) -> DeleteResult:
        """Removes diagram file."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service

            diagram_service.delete_diagram(id)

            return DeleteResult(
                success=True, deleted_id=id, message=f"Deleted diagram: {id}"
            )

        except Exception as e:
            logger.error(f"Failed to delete diagram {id}: {e}")
            return DeleteResult(
                success=False, error=f"Failed to delete diagram: {e!s}"
            )
