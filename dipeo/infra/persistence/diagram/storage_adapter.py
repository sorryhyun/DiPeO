import logging
from typing import Any

from dipeo.core import BaseService
from dipeo.models import DiagramID, DomainDiagram
from dipeo.domain.diagram.services import DiagramBusinessLogic

from .file_repository import DiagramFileRepository

logger = logging.getLogger(__name__)


class DiagramStorageAdapter(BaseService):
    """Infrastructure adapter for diagram storage operations.
    
    This adapter bridges the domain layer with infrastructure storage,
    converting between domain models and storage representations.
    """

    def __init__(
        self, 
        file_repository: DiagramFileRepository,
        domain_service: DiagramBusinessLogic
    ):
        super().__init__()
        self.repository = file_repository
        self.domain_service = domain_service

    async def initialize(self) -> None:
        await self.repository.initialize()

    async def load_diagram(self, diagram_id: DiagramID) -> DomainDiagram:
        """Load a diagram by ID, converting from storage format to domain model."""
        if diagram_id == "quicksave":
            path = "quicksave.json"
        else:
            found_path = await self.repository.find_by_id(diagram_id)
            if not found_path:
                raise FileNotFoundError(f"Diagram not found: {diagram_id}")
            path = found_path

        data = await self.repository.read_file(path)
        # Convert dict to DomainDiagram
        return DomainDiagram(**data)

    async def save_diagram(self, diagram_id: str, diagram: DomainDiagram) -> str:
        """Save a diagram, converting from domain model to storage format."""
        # Convert DomainDiagram to dict for storage
        diagram_data = diagram.model_dump(by_alias=True)
        
        # Determine file path and format
        if diagram_id == "quicksave":
            path = "quicksave.json"
        else:
            path = f"{diagram_id}.json"
            
        await self.repository.write_file(path, diagram_data)
        return path

    async def list_diagrams(self) -> list[dict[str, Any]]:
        """List all available diagrams."""
        return await self.repository.list_files()

    async def delete_diagram(self, diagram_id: str) -> bool:
        """Delete a diagram by ID."""
        if diagram_id == "quicksave":
            path = "quicksave.json"
        else:
            path = await self.repository.find_by_id(diagram_id)
            if not path:
                return False
                
        await self.repository.delete_file(path)
        return True

    async def exists(self, diagram_id: str) -> bool:
        """Check if a diagram exists."""
        if diagram_id == "quicksave":
            return await self.repository.exists("quicksave.json")
        
        path = await self.repository.find_by_id(diagram_id)
        return path is not None