"""Integrated infrastructure service for diagram operations - clean facade implementation."""

import logging
from typing import Any

from dipeo.core.ports.diagram_port import DiagramPort
from dipeo.infra.persistence.diagram import DiagramFileRepository, DiagramLoaderAdapter
from dipeo.models import DiagramFormat, DomainDiagram
from dipeo.domain.diagram.services import DiagramFormatService

logger = logging.getLogger(__name__)


class IntegratedDiagramService(DiagramPort):
    """Facade service that delegates to persistence layer components.
    
    This service acts as a unified interface for diagram operations,
    delegating actual implementation to specialized adapters.
    """
    
    def __init__(self, file_repository: DiagramFileRepository, loader_adapter: DiagramLoaderAdapter):
        self.file_repository = file_repository
        self.loader_adapter = loader_adapter
        self.format_service = DiagramFormatService()
    
    def detect_format(self, content: str) -> DiagramFormat:
        """Delegate format detection to loader adapter."""
        return self.loader_adapter.detect_format(content)
    
    def load_diagram(
        self,
        content: str,
        format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        """Delegate diagram loading to loader adapter."""
        return self.loader_adapter.load_diagram(content, format)
    
    async def load_from_file(
        self,
        file_path: str,
        format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        """Delegate file loading to loader adapter."""
        return await self.loader_adapter.load_from_file(file_path, format)
    
    def list_diagrams(self, directory: str | None = None) -> list[dict[str, Any]]:
        """Delegate listing to file repository.
        
        Note: This is a synchronous wrapper for the async method for backward compatibility.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use run_until_complete
                # This is a limitation that should be addressed by making this method async
                logger.warning("list_diagrams called from async context, consider using async version")
                # For now, we'll have to return empty list or raise an error
                return []
            else:
                return loop.run_until_complete(self.file_repository.list_files())
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.file_repository.list_files())
    
    def list_diagram_files(self, directory: str | None = None) -> list[dict[str, Any]]:
        """Alias for list_diagrams for backward compatibility."""
        return self.list_diagrams(directory)
    
    def save_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        """Save diagram to file."""
        import asyncio
        asyncio.run(self.file_repository.write_file(path, diagram))
    
    def create_diagram(self, name: str, diagram: dict[str, Any], format: str = "json") -> str:
        """Create a new diagram with unique filename."""
        # Determine format from parameter
        if format == "json":
            diagram_format = DiagramFormat.native
        else:
            if diagram.get("format") == "readable" or diagram.get("version") == "readable":
                diagram_format = DiagramFormat.readable
            else:
                diagram_format = DiagramFormat.light
        
        # Get file extension for format
        extension = self.format_service.get_file_extension_for_format(diagram_format)
        filename = f"{name}{extension}"
        
        # Ensure unique filename
        import asyncio
        counter = 1
        while asyncio.run(self.file_repository.exists(filename)):
            filename = f"{name}_{counter}{extension}"
            counter += 1
        
        self.save_diagram(filename, diagram)
        return filename
    
    def update_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        """Update existing diagram."""
        import asyncio
        if not asyncio.run(self.file_repository.exists(path)):
            raise FileNotFoundError(f"Diagram file not found: {path}")
        
        self.save_diagram(path, diagram)
    
    def delete_diagram(self, path: str) -> None:
        """Delete diagram file."""
        import asyncio
        asyncio.run(self.file_repository.delete_file(path))
    
    async def save_diagram_with_id(self, diagram_dict: dict[str, Any], filename: str) -> str:
        """Save diagram with ID."""
        # Determine format from filename
        detected_format = self.format_service.determine_format_from_filename(filename)
        
        # If no format detected and filename doesn't have new extension, add it
        if not detected_format and not any(filename.endswith(ext) for ext in [".native.json", ".light.yaml", ".readable.yaml"]):
            # Default to native format
            filename = f"{filename}.native.json"
        
        await self.file_repository.write_file(filename, diagram_dict)
        
        return diagram_dict.get("id", filename)
    
    async def get_diagram(self, diagram_id: str) -> dict[str, Any] | None:
        """Get diagram by ID."""
        # Use format service to construct search patterns
        search_paths = self.format_service.construct_search_patterns(diagram_id)
        
        for path in search_paths:
            if await self.file_repository.exists(path):
                return await self.file_repository.read_file(path)
        
        # Search all files for matching ID
        all_files = await self.file_repository.list_files()
        for file_info in all_files:
            try:
                diagram = await self.file_repository.read_file(file_info["path"])
                if diagram.get("id") == diagram_id:
                    return diagram
            except Exception:
                continue
        
        return None