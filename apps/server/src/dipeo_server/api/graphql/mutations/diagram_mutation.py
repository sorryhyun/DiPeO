"""GraphQL mutations for diagram management."""

import logging
from datetime import datetime

import strawberry
from dipeo_domain import (
    DiagramMetadata,
    DomainDiagram,
)

from ..context import GraphQLContext
from ..types import (
    CreateDiagramInput,
    DeleteResult,
    DiagramID,
    DiagramResult,
)

logger = logging.getLogger(__name__)


@strawberry.type
class DiagramMutations:
    """Handles diagram CRUD operations."""

    @strawberry.mutation
    async def create_diagram(self, input: CreateDiagramInput, info) -> DiagramResult:
        """Creates new empty diagram."""
        try:
            context: GraphQLContext = info.context

            # Try new services first
            storage_service = context.diagram_storage_service

            # Create metadata directly from input
            metadata = DiagramMetadata(
                name=input.name,
                description=input.description or "",
                author=input.author or "",
                tags=input.tags or [],
                created=datetime.now(),
                modified=datetime.now(),
            )

            diagram_model = DomainDiagram(
                nodes=[],
                arrows=[],
                handles=[],
                persons=[],
                apiKeys=[],
                metadata=metadata,
            )

            # Use new services - convert to storage format
            from dipeo_server.domains.diagram.converters import graphql_to_backend
            backend_model = graphql_to_backend(diagram_model)
            storage_dict = backend_model.model_dump(by_alias=True)
            path = f"{input.name}.json"
            await storage_service.write_file(path, storage_dict)

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
            storage_service = context.diagram_storage_service

            # Use new service
            path = await storage_service.find_by_id(id)
            if path:
                await storage_service.delete_file(path)
            else:
                raise FileNotFoundError(f"Diagram not found: {id}")

            return DeleteResult(
                success=True, deleted_id=id, message=f"Deleted diagram: {id}"
            )

        except Exception as e:
            logger.error(f"Failed to delete diagram {id}: {e}")
            return DeleteResult(
                success=False, error=f"Failed to delete diagram: {e!s}"
            )
