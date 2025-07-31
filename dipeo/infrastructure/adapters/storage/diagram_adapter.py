"""Diagram storage adapter implementing DiagramStoragePort."""

import logging
from typing import BinaryIO
from pathlib import Path
from datetime import datetime

from dipeo.core import BaseService, StorageError
from dipeo.domain.ports.storage import DiagramStoragePort, DiagramInfo, FileSystemPort
from dipeo.domain.diagram.services import DiagramFormatService
from dipeo.infrastructure.services.diagram import DiagramConverterService
from dipeo.models import DiagramFormat

logger = logging.getLogger(__name__)


class DiagramStorageAdapter(BaseService, DiagramStoragePort):
    """Specialized storage adapter for diagram files with format awareness.
    
    This adapter handles the storage of diagrams with different formats:
    - .native.json - Native JSON format
    - .light.yaml - Light YAML format  
    - .readable.yaml - Readable YAML format
    
    It leverages existing domain strategies for format conversion and
    uses FileSystemPort for actual file I/O operations.
    """
    
    def __init__(self, filesystem: FileSystemPort, base_path: str | Path):
        super().__init__()
        self.filesystem = filesystem
        self.base_path = Path(base_path)
        self.format_service = DiagramFormatService()
        self.converter = DiagramConverterService()
        self._initialized = False
    
    async def initialize(self) -> None:
        if self._initialized:
            return
            
        try:
            self.filesystem.mkdir(self.base_path, parents=True)
            await self.converter.initialize()
            self._initialized = True
            logger.info(f"DiagramStorageAdapter initialized at: {self.base_path}")
        except Exception as e:
            raise StorageError(f"Failed to initialize diagram storage: {e}")
    
    def _get_diagram_path(self, diagram_id: str, format: str | None = None) -> Path:
        supported_extensions = [".native.json", ".light.yaml", ".light.yml", 
                              ".readable.yaml", ".readable.yml", ".json", ".yaml", ".yml"]
        
        for ext in supported_extensions:
            if diagram_id.endswith(ext):
                path = self.base_path / diagram_id
                if self.filesystem.exists(path):
                    return path
                return path
        
        if format:
            format_enum = self._format_string_to_enum(format)
            extension = self.format_service.get_file_extension_for_format(format_enum)
            return self.base_path / f"{diagram_id}{extension}"
        
        patterns = self.format_service.construct_search_patterns(diagram_id)
        for pattern in patterns:
            path = self.base_path / pattern
            if self.filesystem.exists(path):
                return path
        
        return self.base_path / f"{diagram_id}.native.json"
    
    def _format_string_to_enum(self, format: str) -> DiagramFormat:
        format_map = {
            "native": DiagramFormat.NATIVE,
            "light": DiagramFormat.LIGHT,
            "readable": DiagramFormat.READABLE,
            "json": DiagramFormat.NATIVE,
            "yaml": DiagramFormat.LIGHT,
        }
        return format_map.get(format.lower(), DiagramFormat.NATIVE)
    
    def _detect_format_from_path(self, path: Path) -> str:
        format_enum = self.format_service.determine_format_from_filename(str(path))
        if format_enum:
            return format_enum.value
        return "native"
    
    async def save_diagram(self, diagram_id: str, content: str, format: str) -> DiagramInfo:
        if not self._initialized:
            await self.initialize()
            
        try:
            path = self._get_diagram_path(diagram_id, format)
            
            self.filesystem.mkdir(path.parent, parents=True)
            
            format_enum = self._format_string_to_enum(format)
            self.format_service.validate_format(content, format_enum)
            
            with self.filesystem.open(path, "wb") as f:
                f.write(content.encode('utf-8'))
            
            stat = self.filesystem.stat(path)
            rel_path = path.relative_to(self.base_path)
            
            return DiagramInfo(
                id=str(rel_path).replace('\\', '/'),
                path=rel_path,
                format=format,
                size=stat.size,
                modified=stat.modified,
                created=stat.created
            )
            
        except Exception as e:
            raise StorageError(f"Failed to save diagram {diagram_id}: {e}")
    
    async def load_diagram(self, diagram_id: str) -> tuple[str, str]:
        if not self._initialized:
            await self.initialize()
            
        try:
            path = self._get_diagram_path(diagram_id)
            
            if not self.filesystem.exists(path):
                raise StorageError(f"Diagram not found: {diagram_id}")
            
            with self.filesystem.open(path, "rb") as f:
                content = f.read().decode('utf-8')
            
            format = self._detect_format_from_path(path)
            
            return content, format
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load diagram {diagram_id}: {e}")
    
    async def exists(self, diagram_id: str) -> bool:
        if not self._initialized:
            await self.initialize()
            
        supported_extensions = [".native.json", ".light.yaml", ".light.yml", 
                              ".readable.yaml", ".readable.yml", ".json", ".yaml", ".yml"]
        
        for ext in supported_extensions:
            if diagram_id.endswith(ext):
                path = self.base_path / diagram_id
                return self.filesystem.exists(path)
        
        patterns = self.format_service.construct_search_patterns(diagram_id)
        for pattern in patterns:
            path = self.base_path / pattern
            if self.filesystem.exists(path):
                return True
        return False
    
    async def delete(self, diagram_id: str) -> None:
        if not self._initialized:
            await self.initialize()
            
        try:
            path = self._get_diagram_path(diagram_id)
            
            if not self.filesystem.exists(path):
                raise StorageError(f"Diagram not found: {diagram_id}")
            
            self.filesystem.remove(path)
            logger.debug(f"Deleted diagram: {diagram_id}")
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete diagram {diagram_id}: {e}")
    
    async def list_diagrams(self, format: str | None = None) -> list[DiagramInfo]:
        if not self._initialized:
            await self.initialize()
            
        diagrams = []
        
        if format:
            format_enum = self._format_string_to_enum(format)
            extensions = [self.format_service.get_file_extension_for_format(format_enum)]
        else:
            extensions = [".native.json", ".light.yaml", ".readable.yaml"]
        
        try:
            def scan_directory(dir_path: Path) -> None:
                try:
                    items = self.filesystem.listdir(dir_path)
                except Exception:
                    return
                    
                for item in items:
                    if item.is_file():
                        for ext in extensions:
                            if str(item).endswith(ext):
                                stat = self.filesystem.stat(item)
                                
                                rel_path = item.relative_to(self.base_path)
                                
                                diagram_id = str(rel_path).replace('\\', '/')
                                
                                diagrams.append(DiagramInfo(
                                    id=diagram_id,
                                    path=rel_path,
                                    format=self._detect_format_from_path(item),
                                    size=stat.size,
                                    modified=stat.modified,
                                    created=stat.created
                                ))
                                break
                    elif item.is_dir():
                        scan_directory(item)
            
            scan_directory(self.base_path)
        except Exception as e:
            raise StorageError(f"Failed to list diagrams: {e}")
        
        diagrams.sort(key=lambda x: x.modified, reverse=True)
        return diagrams
    
    async def get_info(self, diagram_id: str) -> DiagramInfo | None:
        if not self._initialized:
            await self.initialize()
            
        try:
            path = self._get_diagram_path(diagram_id)
            
            if not self.filesystem.exists(path):
                return None
            
            stat = self.filesystem.stat(path)
            rel_path = path.relative_to(self.base_path)
            
            return DiagramInfo(
                id=str(rel_path).replace('\\', '/'),
                path=rel_path,
                format=self._detect_format_from_path(path),
                size=stat.size,
                modified=stat.modified,
                created=stat.created
            )
            
        except Exception as e:
            logger.warning(f"Failed to get info for diagram {diagram_id}: {e}")
            return None
    
    async def convert_format(self, diagram_id: str, target_format: str) -> DiagramInfo:
        if not self._initialized:
            await self.initialize()
            
        try:
            content, current_format = await self.load_diagram(diagram_id)
            
            if current_format == target_format:
                info = await self.get_info(diagram_id)
                if info:
                    return info
                raise StorageError(f"Failed to get info for diagram {diagram_id}")
            
            diagram = self.converter.deserialize(content, current_format)
            
            new_content = self.converter.serialize(diagram, target_format)
            
            await self.delete(diagram_id)
            
            return await self.save_diagram(diagram_id, new_content, target_format)
            
        except Exception as e:
            raise StorageError(f"Failed to convert diagram {diagram_id} to {target_format}: {e}")