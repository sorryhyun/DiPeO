"""Diagram mutations using UnifiedServiceRegistry."""

import logging
from datetime import datetime

import strawberry

from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey
from dipeo.diagram_generated import DiagramMetadata, DomainDiagram
from dipeo.domain.diagram.utils import domain_diagram_to_dict

from dipeo.diagram_generated.domain_models import DiagramID
from ...types.inputs import CreateDiagramInput
from ...types.results import DiagramResult, DeleteResult

logger = logging.getLogger(__name__)

# Service keys
INTEGRATED_DIAGRAM_SERVICE = ServiceKey("integrated_diagram_service")


def create_diagram_mutations(registry: UnifiedServiceRegistry) -> type:
    """Create diagram mutation methods with injected service registry."""
    
    @strawberry.type
    class DiagramMutations:
        @strawberry.mutation
        async def create_diagram(self, input: CreateDiagramInput) -> DiagramResult:
            try:
                integrated_service = registry.require(INTEGRATED_DIAGRAM_SERVICE)
                
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
                
                # Convert to storage format and save
                storage_dict = domain_diagram_to_dict(diagram_model)
                filename = await integrated_service.create_diagram(
                    input.name, storage_dict, "json"
                )
                
                return DiagramResult(
                    success=True,
                    diagram=diagram_model,
                    message=f"Created diagram: {filename}",
                )
                
            except ValueError as e:
                logger.error(f"Validation error creating diagram: {e}")
                return DiagramResult(success=False, error=f"Validation error: {str(e)}")
            except Exception as e:
                logger.error(f"Failed to create diagram: {e}")
                return DiagramResult(
                    success=False, error=f"Failed to create diagram: {str(e)}"
                )
        
        @strawberry.mutation
        async def delete_diagram(self, id: strawberry.ID) -> DeleteResult:
            try:
                diagram_id = DiagramID(str(id))
                integrated_service = registry.require(INTEGRATED_DIAGRAM_SERVICE)
                
                # Get diagram to verify it exists
                diagram_data = await integrated_service.get_diagram(diagram_id)
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
                    success=True, 
                    deleted_id=str(diagram_id), 
                    message=f"Deleted diagram: {diagram_id}"
                )
                
            except Exception as e:
                logger.error(f"Failed to delete diagram {diagram_id}: {e}")
                return DeleteResult(
                    success=False, 
                    error=f"Failed to delete diagram: {str(e)}"
                )
    
    return DiagramMutations