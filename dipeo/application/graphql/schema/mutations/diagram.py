"""Diagram mutations using ServiceRegistry."""

import logging
from datetime import datetime

import strawberry

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_PORT
from dipeo.diagram_generated import DiagramMetadata, DomainDiagram
from dipeo.diagram_generated.domain_models import DiagramID
from dipeo.diagram_generated.graphql.inputs import CreateDiagramInput

from ...types.results import DeleteResult, DiagramResult

logger = logging.getLogger(__name__)


def create_diagram_mutations(registry: ServiceRegistry) -> type:
    """Create diagram mutation methods with injected service registry."""

    @strawberry.type
    class DiagramMutations:
        @strawberry.mutation
        async def create_diagram(self, input: CreateDiagramInput) -> DiagramResult:
            try:
                diagram_service = registry.resolve(DIAGRAM_PORT)

                # Create metadata from input
                metadata = DiagramMetadata(
                    name=input.name,
                    description=input.description or "",
                    author=input.author or "",
                    tags=input.tags or [],
                    created=datetime.now(),
                    modified=datetime.now(),
                )

                # Create empty diagram with metadata
                diagram_model = DomainDiagram(
                    nodes=[],
                    arrows=[],
                    handles=[],
                    persons=[],
                    apiKeys=[],
                    metadata=metadata,
                )

                # Save the typed model directly
                filename = await diagram_service.create_diagram(input.name, diagram_model, "json")

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
                return DiagramResult(success=False, error=f"Failed to create diagram: {e!s}")

        @strawberry.mutation
        async def delete_diagram(self, id: strawberry.ID) -> DeleteResult:
            try:
                diagram_id = DiagramID(str(id))
                diagram_service = registry.resolve(DIAGRAM_PORT)

                # Get diagram to verify it exists
                diagram_data = await diagram_service.get_diagram(diagram_id)
                if not diagram_data:
                    raise FileNotFoundError(f"Diagram not found: {id}")

                # Find the path for deletion
                file_repo = diagram_service.file_repository
                path = await file_repo.find_by_id(id)
                if path:
                    await diagram_service.delete_diagram(path)
                else:
                    raise FileNotFoundError(f"Diagram path not found: {id}")

                return DeleteResult(
                    success=True,
                    deleted_id=str(diagram_id),
                    message=f"Deleted diagram: {diagram_id}",
                )

            except Exception as e:
                logger.error(f"Failed to delete diagram {diagram_id}: {e}")
                return DeleteResult(success=False, error=f"Failed to delete diagram: {e!s}")

    return DiagramMutations
