import logging
from typing import Any, Dict

from dipeo_core import BaseService
from dipeo_domain import DiagramID

from .storage_service import DiagramStorageService

logger = logging.getLogger(__name__)


class DiagramStorageAdapter(BaseService):
    """Simple adapter for diagram storage operations."""

    def __init__(self, storage_service: DiagramStorageService):
        super().__init__()
        self.storage = storage_service

    async def initialize(self) -> None:
        await self.storage.initialize()

    async def load_diagram(self, diagram_id: DiagramID) -> Dict[str, Any]:
        if diagram_id == "quicksave":
            path = "quicksave.json"
        else:
            found_path = await self.storage.find_by_id(diagram_id)
            if not found_path:
                raise FileNotFoundError(f"Diagram not found: {diagram_id}")
            path = found_path

        return await self.storage.read_file(path)

    async def save_diagram(self, diagram_id: str, diagram_data: Dict[str, Any]) -> str:
        await self.storage.write_file(f"{diagram_id}.json", diagram_data)
        return f"{diagram_id}.json"

    async def list_diagrams(self) -> list:
        """List all available diagrams."""
        return await self.storage.list_files()

    async def delete_diagram(self, diagram_id: str) -> bool:
        path = await self.storage.find_by_id(diagram_id)
        if path:
            await self.storage.delete_file(path)
            return True
        return False

