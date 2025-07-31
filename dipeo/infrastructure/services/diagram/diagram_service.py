"""Main diagram service orchestrating storage and conversion operations."""

import logging
from typing import Any
from pathlib import Path

from dipeo.core import BaseService
from dipeo.core.ports.diagram_port import DiagramPort
from dipeo.domain.ports.storage import DiagramStoragePort
from dipeo.domain.diagram.services import DiagramFormatService
from dipeo.domain.diagram.utils import dict_to_domain_diagram
from dipeo.models import DiagramFormat, DomainDiagram
from .converter_service import DiagramConverterService

logger = logging.getLogger(__name__)


class DiagramService(BaseService, DiagramPort):
    """High-level service for diagram operations.
    
    This service orchestrates diagram storage and format conversion,
    providing a clean interface for diagram management operations.
    It replaces the old IntegratedDiagramService with a cleaner design.
    """
    
    def __init__(
        self,
        storage: DiagramStoragePort,
        converter: DiagramConverterService | None = None
    ):
        super().__init__()
        self.storage = storage
        self.converter = converter or DiagramConverterService()
        self.format_service = DiagramFormatService()
        self._initialized = False
    
    async def initialize(self) -> None:
        if self._initialized:
            return
            
        await self.storage.initialize()
        await self.converter.initialize()
        
        self._initialized = True
        logger.info("DiagramService initialized")
    
    def detect_format(self, content: str) -> DiagramFormat:
        format_id = self.converter.detect_format(content)
        if not format_id:
            raise ValueError("Unable to detect diagram format")
        
        return self._format_string_to_enum(format_id)
    
    def load_diagram(
        self,
        content: str,
        format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        format_id = format.value if format else None
        return self.converter.deserialize(content, format_id)
    
    async def load_from_file(
        self,
        file_path: str,
        format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        """Load diagram from file.
        
        Args:
            file_path: Path to diagram file
            format: Expected format, or None to auto-detect
            
        Returns:
            Domain diagram object
        """
        if not self._initialized:
            await self.initialize()
            
        # Extract diagram ID from path, preserving directory structure
        path = Path(file_path)
        
        # If path contains 'files/', extract relative path from there
        path_parts = path.parts
        if "files" in path_parts:
            idx = path_parts.index("files")
            rel_path = Path(*path_parts[idx+1:])
        else:
            rel_path = path
        
        # Remove extension to get diagram ID
        diagram_id = str(rel_path.with_suffix(""))
        
        # Remove format suffixes from ID
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        # Load from storage
        content, format_str = await self.storage.load_diagram(diagram_id)
        
        # Verify format if specified
        if format:
            detected_format = self._format_string_to_enum(format_str)
            if detected_format != format:
                raise ValueError(
                    f"Format mismatch: expected {format.value}, "
                    f"got {detected_format.value}"
                )
        
        return self.load_diagram(content, format)
    
    async def load_from_string(
        self,
        content: str,
        format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        """Load diagram from string content.
        
        Args:
            content: Diagram content string
            format: Expected format, or None to auto-detect
            
        Returns:
            Domain diagram object
        """
        return self.load_diagram(content, format)
    
    async def list_diagrams(self, directory: str | None = None) -> list[dict[str, Any]]:
        """List all available diagrams.
        
        Args:
            directory: Filter by directory (not used in storage adapter)
            
        Returns:
            List of diagram metadata
        """
        if not self._initialized:
            await self.initialize()
            
        diagram_infos = await self.storage.list_diagrams()
        
        # Convert to expected format
        diagrams = []
        for info in diagram_infos:
            # Extract filename from path for name
            name = Path(info.id).name if info.id else "unknown"
            
            diagrams.append({
                "id": info.id,
                "path": str(info.path),
                "name": name,
                "format": info.format,
                "size": info.size,
                "modified": info.modified.isoformat() if info.modified else None,
                "created": info.created.isoformat() if info.created else None,
            })
        
        return diagrams
    
    async def save_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        """Save diagram to storage.
        
        Args:
            path: File path (used to determine format and ID)
            diagram: Diagram data dictionary
        """
        if not self._initialized:
            await self.initialize()
            
        # Extract diagram ID and format from path
        path_obj = Path(path)
        diagram_id = path_obj.stem
        
        # Remove format suffixes
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        # Determine format from filename
        format = self.format_service.determine_format_from_filename(path)
        if not format:
            format = DiagramFormat.NATIVE  # Default
        
        # Convert dict to domain model
        domain_diagram = dict_to_domain_diagram(diagram)
        
        # Serialize to string
        content = self.converter.serialize(domain_diagram, format.value)
        
        # Save to storage
        await self.storage.save_diagram(diagram_id, content, format.value)
    
    async def create_diagram(
        self, name: str, diagram: dict[str, Any], format: str = "json"
    ) -> str:
        """Create a new diagram with unique filename.
        
        Args:
            name: Base name for diagram
            diagram: Diagram data
            format: Format hint (json/yaml)
            
        Returns:
            Created diagram ID
        """
        if not self._initialized:
            await self.initialize()
            
        # Determine format
        if format == "json":
            diagram_format = DiagramFormat.NATIVE
        elif diagram.get("format") == "readable" or diagram.get("version") == "readable":
            diagram_format = DiagramFormat.READABLE
        else:
            diagram_format = DiagramFormat.LIGHT
        
        # Ensure unique ID
        diagram_id = name
        counter = 1
        while await self.storage.exists(diagram_id):
            diagram_id = f"{name}_{counter}"
            counter += 1
        
        # Convert and save
        domain_diagram = dict_to_domain_diagram(diagram)
        content = self.converter.serialize(domain_diagram, diagram_format.value)
        await self.storage.save_diagram(diagram_id, content, diagram_format.value)
        
        return diagram_id
    
    async def update_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        """Update existing diagram.
        
        Args:
            path: Diagram file path
            diagram: Updated diagram data
        """
        # Save handles updates
        await self.save_diagram(path, diagram)
    
    async def update_diagram_by_id(self, diagram_id: str, diagram: dict[str, Any]) -> None:
        """Update diagram by ID.
        
        Args:
            diagram_id: Diagram identifier
            diagram: Updated diagram data
        """
        if not self._initialized:
            await self.initialize()
            
        # Check if diagram exists
        if not await self.storage.exists(diagram_id):
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")
        
        # Get current format
        info = await self.storage.get_info(diagram_id)
        if not info:
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")
        
        # Convert and save
        domain_diagram = dict_to_domain_diagram(diagram)
        content = self.converter.serialize(domain_diagram, info.format)
        await self.storage.save_diagram(diagram_id, content, info.format)
    
    async def delete_diagram(self, path: str) -> None:
        """Delete diagram by path.
        
        Args:
            path: Diagram file path
        """
        if not self._initialized:
            await self.initialize()
            
        # Extract ID from path
        path_obj = Path(path)
        diagram_id = path_obj.stem
        
        # Remove format suffixes
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        await self.storage.delete(diagram_id)
    
    async def save_diagram_with_id(
        self, diagram_dict: dict[str, Any], filename: str
    ) -> str:
        """Save diagram ensuring it has an ID.
        
        Args:
            diagram_dict: Diagram data
            filename: Target filename
            
        Returns:
            Diagram ID
        """
        if not self._initialized:
            await self.initialize()
            
        # Extract ID from filename
        path_obj = Path(filename)
        diagram_id = path_obj.stem
        
        # Remove format suffixes
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        # Ensure diagram has ID
        if "id" not in diagram_dict:
            diagram_dict["id"] = diagram_id
        
        # Save diagram
        await self.save_diagram(filename, diagram_dict)
        
        return diagram_dict.get("id", diagram_id)
    
    async def get_diagram(self, diagram_id: str) -> dict[str, Any] | None:
        """Get diagram by ID.
        
        Args:
            diagram_id: Diagram identifier
            
        Returns:
            Diagram data or None if not found
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            content, format_str = await self.storage.load_diagram(diagram_id)
            diagram = self.converter.deserialize(content, format_str)
            return diagram.model_dump(by_alias=True)
        except Exception as e:
            logger.warning(f"Failed to get diagram {diagram_id}: {e}")
            return None
    
    async def convert_diagram_format(
        self, diagram_id: str, target_format: DiagramFormat
    ) -> None:
        """Convert diagram to different format.
        
        Args:
            diagram_id: Diagram identifier
            target_format: Target format
        """
        if not self._initialized:
            await self.initialize()
            
        await self.storage.convert_format(diagram_id, target_format.value)
    
    def _format_string_to_enum(self, format_str: str) -> DiagramFormat:
        """Convert format string to enum.
        
        Args:
            format_str: Format string
            
        Returns:
            DiagramFormat enum value
        """
        format_map = {
            "native": DiagramFormat.NATIVE,
            "light": DiagramFormat.LIGHT,
            "readable": DiagramFormat.READABLE,
        }
        return format_map.get(format_str, DiagramFormat.NATIVE)