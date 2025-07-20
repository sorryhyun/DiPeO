"""Integrated infrastructure service for diagram operations - clean facade implementation.

This module provides a unified async interface for diagram operations,
delegating to specialized persistence layer components.
"""

import logging
from typing import Any

from dipeo.core.ports.diagram_port import DiagramPort
from dipeo.infra.persistence.diagram import DiagramFileRepository, DiagramLoaderAdapter
from dipeo.models import DiagramFormat, Diagram
from dipeo.domain.diagram.services import DiagramFormatService
from dipeo.infra.diagram.unified_converter import converter_registry
from dipeo.domain.diagram.utils import dict_to_domain_diagram

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
    ) -> Diagram:
        """Delegate diagram loading to loader adapter."""
        return self.loader_adapter.load_diagram(content, format)
    
    async def load_from_file(
        self,
        file_path: str,
        format: DiagramFormat | None = None,
    ) -> Diagram:
        """Delegate file loading to loader adapter."""
        return await self.loader_adapter.load_from_file(file_path, format)
    
    async def list_diagrams(self, directory: str | None = None) -> list[dict[str, Any]]:
        return await self.file_repository.list_files()
    
    async def save_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        # Determine format from filename
        format = self.format_service.determine_format_from_filename(path)
        
        # For YAML formats, use converter to get properly formatted string
        if format in [DiagramFormat.light, DiagramFormat.readable]:
            # Convert dict to domain model
            domain_diagram = dict_to_domain_diagram(diagram)
            
            # Use converter to serialize with proper formatting
            content_str = converter_registry.serialize(domain_diagram, format.value)
            
            # Write the formatted string directly
            file_path = self.file_repository.diagrams_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content_str, encoding="utf-8")
        else:
            # For JSON formats, use the existing method
            await self.file_repository.write_file(path, diagram)
    
    async def create_diagram(self, name: str, diagram: dict[str, Any], format: str = "json") -> str:
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
        counter = 1
        while await self.file_repository.exists(filename):
            filename = f"{name}_{counter}{extension}"
            counter += 1
        
        await self.save_diagram(filename, diagram)
        return filename
    
    async def update_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        """Update existing diagram."""
        if not await self.file_repository.exists(path):
            raise FileNotFoundError(f"Diagram file not found: {path}")
        
        await self.save_diagram(path, diagram)
    
    async def update_diagram_by_id(self, diagram_id: str, diagram: dict[str, Any]) -> None:
        """Update diagram by ID."""
        # Find the path for this diagram ID
        path = await self.file_repository.find_by_id(diagram_id)
        if not path:
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")
        
        await self.update_diagram(path, diagram)
    
    async def delete_diagram(self, path: str) -> None:
        await self.file_repository.delete_file(path)
    
    async def save_diagram_with_id(self, diagram_dict: dict[str, Any], filename: str) -> str:
        """Save diagram with ID."""
        # Determine format from filename
        detected_format = self.format_service.determine_format_from_filename(filename)
        
        # If no format detected and filename doesn't have new extension, add it
        if not detected_format and not any(filename.endswith(ext) for ext in [".native.json", ".light.yaml", ".readable.yaml"]):
            # Default to native format
            filename = f"{filename}.native.json"
        
        # Ensure the diagram has an ID
        if "id" not in diagram_dict:
            diagram_dict["id"] = filename.split(".")[0]
        
        # Use save_diagram to ensure proper formatting
        await self.save_diagram(filename, diagram_dict)
        
        return diagram_dict.get("id", filename)
    
    async def get_diagram(self, diagram_id: str) -> dict[str, Any] | None:
        """Get diagram by ID."""
        # First try to find by ID using repository
        path = await self.file_repository.find_by_id(diagram_id)
        if path:
            return await self.file_repository.read_file(path)
        
        return None