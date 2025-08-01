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
    """High-level service orchestrating diagram storage and format conversion."""
    
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
    
    async def list_diagrams(self, directory: str | None = None) -> list[dict[str, Any]]:
        if not self._initialized:
            await self.initialize()
            
        diagram_infos = await self.storage.list_diagrams()
        
        diagrams = []
        for info in diagram_infos:
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
        if not self._initialized:
            await self.initialize()
            
        path_obj = Path(path)
        diagram_id = path_obj.stem
        
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        format = self.format_service.determine_format_from_filename(path)
        if not format:
            format = DiagramFormat.NATIVE
        
        domain_diagram = dict_to_domain_diagram(diagram)
        content = self.converter.serialize(domain_diagram, format.value)
        await self.storage.save_diagram(diagram_id, content, format.value)
    
    async def create_diagram(
        self, name: str, diagram: dict[str, Any], format: str = "json"
    ) -> str:
        if not self._initialized:
            await self.initialize()
            
        if format == "json":
            diagram_format = DiagramFormat.NATIVE
        elif diagram.get("format") == "readable" or diagram.get("version") == "readable":
            diagram_format = DiagramFormat.READABLE
        else:
            diagram_format = DiagramFormat.LIGHT
        
        diagram_id = name
        counter = 1
        while await self.storage.exists(diagram_id):
            diagram_id = f"{name}_{counter}"
            counter += 1
        
        domain_diagram = dict_to_domain_diagram(diagram)
        content = self.converter.serialize(domain_diagram, diagram_format.value)
        await self.storage.save_diagram(diagram_id, content, diagram_format.value)
        
        return diagram_id
    
    async def update_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        await self.save_diagram(path, diagram)
    
    async def update_diagram_by_id(self, diagram_id: str, diagram: dict[str, Any]) -> None:
        if not self._initialized:
            await self.initialize()
            
        if not await self.storage.exists(diagram_id):
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")
        
        info = await self.storage.get_info(diagram_id)
        if not info:
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")
        
        domain_diagram = dict_to_domain_diagram(diagram)
        content = self.converter.serialize(domain_diagram, info.format)
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
    
    async def save_diagram_with_id(
        self, diagram_dict: dict[str, Any], filename: str
    ) -> str:
        if not self._initialized:
            await self.initialize()
            
        path_obj = Path(filename)
        diagram_id = path_obj.stem
        
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        if "id" not in diagram_dict:
            diagram_dict["id"] = diagram_id
        
        await self.save_diagram(filename, diagram_dict)
        
        return diagram_dict.get("id", diagram_id)
    
    async def get_diagram(self, diagram_id: str) -> dict[str, Any] | None:
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