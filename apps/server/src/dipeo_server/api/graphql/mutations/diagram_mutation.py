"""GraphQL mutations for diagram management."""

import logging
from datetime import datetime

import strawberry
from dipeo.models import (
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
    # Handles diagram CRUD operations

    @strawberry.mutation
    async def create_diagram(self, input: CreateDiagramInput, info) -> DiagramResult:
        try:
            context: GraphQLContext = info.context

            # Use integrated diagram service
            integrated_service = context.get_service("integrated_diagram_service")

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

            # Use integrated service - convert to storage format
            from dipeo.domain.diagram.utils import domain_diagram_to_dict

            storage_dict = domain_diagram_to_dict(diagram_model)
            filename = await integrated_service.create_diagram(input.name, storage_dict, "json")

            # Use domain model directly
            return DiagramResult(
                success=True,
                diagram=diagram_model,
                message=f"Created diagram: {filename}",
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
        try:
            context: GraphQLContext = info.context
            integrated_service = context.get_service("integrated_diagram_service")

            # Use integrated service to find and delete
            diagram_data = await integrated_service.get_diagram(id)
            if not diagram_data:
                raise FileNotFoundError(f"Diagram not found: {id}")

            # Find the path for deletion
            file_repo = integrated_service.file_repository
            path = await file_repo.find_by_id(id)
            if path:
                await integrated_service.delete_diagram(path)
            else:
                raise FileNotFoundError(f"Diagram path not found: {id}")

            return DeleteResult(
                success=True, deleted_id=id, message=f"Deleted diagram: {id}"
            )

        except Exception as e:
            logger.error(f"Failed to delete diagram {id}: {e}")
            return DeleteResult(success=False, error=f"Failed to delete diagram: {e!s}")
