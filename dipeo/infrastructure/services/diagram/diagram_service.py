"""Main diagram service orchestrating storage and conversion operations."""

import logging
from pathlib import Path

from dipeo.core import BaseService
from dipeo.core.ports.diagram_port import DiagramPort
from dipeo.domain.ports.storage import DiagramStoragePort, DiagramInfo
from dipeo.domain.diagram.services import DiagramFormatDetector
from dipeo.diagram_generated import DiagramFormat, DomainDiagram
from .converter_service import DiagramConverterService

logger = logging.getLogger(__name__)


class DiagramService(BaseService, DiagramPort):
    """High-level service orchestrating diagram storage and format conversion."""
    
    def __init__(
        self,
        storage: DiagramStoragePort,
        converter: DiagramConverterService | None = None
    ):
        super().__init__()
        self.storage = storage
        self.converter = converter or DiagramConverterService()
        self.format_detector = DiagramFormatDetector()
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
        if not self._initialized:
            await self.initialize()
            
        path = Path(file_path)
        
        if "files" in path.parts:
            idx = path.parts.index("files")
            rel_path = Path(*path.parts[idx+1:])
        else:
            rel_path = path
        
        diagram_id = str(rel_path.with_suffix(""))
        
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        content, format_str = await self.storage.load_diagram(diagram_id)
        
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
        return self.load_diagram(content, format)
    
    async def list_diagrams(self, directory: str | None = None) -> list[DiagramInfo]:
        if not self._initialized:
            await self.initialize()
            
        # Return metadata only for efficient listing
        return await self.storage.list_diagrams()
    
    async def save_diagram(self, path: str, diagram: DomainDiagram) -> None:
        if not self._initialized:
            await self.initialize()
            
        path_obj = Path(path)
        diagram_id = path_obj.stem
        
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        format_enum = self.format_detector.detect_format_from_filename(path)
        if not format_enum:
            format_enum = DiagramFormat.NATIVE
        
        content = self.converter.serialize(diagram, format_enum.value)
        await self.storage.save_diagram(diagram_id, content, format_enum.value)
    
    async def create_diagram(
        self, name: str, diagram: DomainDiagram, format_str: str = "native"
    ) -> str:
        if not self._initialized:
            await self.initialize()
            
        if format_str == "native" or format_str == "json":
            diagram_format = DiagramFormat.NATIVE
        elif format_str == "readable":
            diagram_format = DiagramFormat.READABLE
        elif format_str == "light":
            diagram_format = DiagramFormat.LIGHT
        else:
            diagram_format = DiagramFormat.NATIVE
        
        diagram_id = name
        counter = 1
        while await self.storage.exists(diagram_id):
            diagram_id = f"{name}_{counter}"
            counter += 1
        
        content = self.converter.serialize(diagram, diagram_format.value)
        await self.storage.save_diagram(diagram_id, content, diagram_format.value)
        
        return diagram_id
    
    async def update_diagram(self, diagram_id: str, diagram: DomainDiagram) -> None:
        if not self._initialized:
            await self.initialize()
            
        if not await self.storage.exists(diagram_id):
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")
        
        info = await self.storage.get_info(diagram_id)
        if not info:
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")
        
        content = self.converter.serialize(diagram, info.format)
        await self.storage.save_diagram(diagram_id, content, info.format)
    
    
    async def delete_diagram(self, path: str) -> None:
        if not self._initialized:
            await self.initialize()
            
        path_obj = Path(path)
        diagram_id = path_obj.stem
        
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        await self.storage.delete(diagram_id)
    
    
    async def get_diagram(self, diagram_id: str) -> DomainDiagram | None:
        """Get diagram by its ID.
        
        Returns:
            DomainDiagram if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Use the new typed method if available
            if hasattr(self.storage, 'load_diagram_model'):
                return await self.storage.load_diagram_model(diagram_id)
            else:
                # Fallback to deserializing from content
                content, format_str = await self.storage.load_diagram(diagram_id)
                return self.converter.deserialize(content, format_str)
        except Exception as e:
            logger.warning(f"Failed to get diagram {diagram_id}: {e}")
            return None
    
    async def convert_diagram_format(
        self, diagram_id: str, target_format: DiagramFormat
    ) -> None:
        if not self._initialized:
            await self.initialize()
            
        await self.storage.convert_format(diagram_id, target_format.value)
    
    def _format_string_to_enum(self, format_str: str) -> DiagramFormat:
        format_map = {
            "native": DiagramFormat.NATIVE,
            "light": DiagramFormat.LIGHT,
            "readable": DiagramFormat.READABLE,
        }
        return format_map.get(format_str, DiagramFormat.NATIVE)