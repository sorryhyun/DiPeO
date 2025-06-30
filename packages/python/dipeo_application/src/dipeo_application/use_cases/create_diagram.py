"""Use case for creating diagrams."""

from typing import TYPE_CHECKING, Any
from dipeo_core import BaseService, Result, Error
from dipeo_domain.models import DomainDiagram
from datetime import UTC, datetime
import uuid

if TYPE_CHECKING:
    from dipeo_domain.domains.diagram.services import DiagramStorageAdapter
    from dipeo_domain.domains.validation import ValidationDomainService


class CreateDiagramUseCase(BaseService):
    """Use case for creating new diagrams."""
    
    def __init__(
        self,
        diagram_storage: "DiagramStorageAdapter",
        validation_service: "ValidationDomainService",
    ):
        """Initialize with required services."""
        super().__init__()
        self.diagram_storage = diagram_storage
        self.validation_service = validation_service
    
    async def execute(self, diagram_data: dict[str, Any]) -> Result[DomainDiagram, Error]:
        """Create a new diagram.
        
        Args:
            diagram_data: Raw diagram data
            
        Returns:
            Result containing created diagram or error
        """
        # Validate diagram structure
        validation_result = await self.validation_service.validate_diagram(diagram_data)
        if not validation_result.get("success"):
            return Result.err(Error(
                code="INVALID_DIAGRAM",
                message=validation_result.get("error", "Invalid diagram structure"),
                details=validation_result.get("details")
            ))
        
        # Create diagram model
        try:
            # Add metadata if not present
            if "metadata" not in diagram_data:
                diagram_data["metadata"] = {}
            
            # Generate ID if not present
            if "id" not in diagram_data["metadata"]:
                diagram_data["metadata"]["id"] = str(uuid.uuid4())
            
            # Set timestamps
            now = datetime.now(UTC).isoformat()
            diagram_data["metadata"]["created"] = now
            diagram_data["metadata"]["updated"] = now
            
            # Create domain model
            diagram = DomainDiagram.model_validate(diagram_data)
            
        except Exception as e:
            return Result.err(Error(
                code="MODEL_VALIDATION_ERROR",
                message=f"Failed to create diagram model: {str(e)}"
            ))
        
        # Save diagram
        try:
            save_result = await self.diagram_storage.save_diagram(
                diagram_id=diagram.metadata.id,
                diagram=diagram.model_dump()
            )
            
            if not save_result.get("success"):
                return Result.err(Error(
                    code="SAVE_ERROR",
                    message=save_result.get("error", "Failed to save diagram")
                ))
            
            return Result.ok(diagram)
            
        except Exception as e:
            return Result.err(Error(
                code="STORAGE_ERROR",
                message=f"Failed to save diagram: {str(e)}"
            ))