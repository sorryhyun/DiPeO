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
        """Initialize diagram storage adapter.
        
        Args:
            filesystem: FileSystem adapter for I/O operations
            base_path: Base directory for diagram storage
        """
        super().__init__()
        self.filesystem = filesystem
        self.base_path = Path(base_path)
        self.format_service = DiagramFormatService()
        self.converter = DiagramConverterService()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize storage directory and converter."""
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
        """Get path for diagram with appropriate extension."""
        if format:
            # Map format to DiagramFormat enum
            format_enum = self._format_string_to_enum(format)
            extension = self.format_service.get_file_extension_for_format(format_enum)
            return self.base_path / f"{diagram_id}{extension}"
        
        # Try to find existing file with any supported extension
        patterns = self.format_service.construct_search_patterns(diagram_id)
        for pattern in patterns:
            path = self.base_path / pattern
            if self.filesystem.exists(path):
                return path
        
        # Default to native format if not found
        return self.base_path / f"{diagram_id}.native.json"
    
    def _format_string_to_enum(self, format: str) -> DiagramFormat:
        """Convert format string to DiagramFormat enum."""
        format_map = {
            "native": DiagramFormat.NATIVE,
            "light": DiagramFormat.LIGHT,
            "readable": DiagramFormat.READABLE,
            "json": DiagramFormat.NATIVE,
            "yaml": DiagramFormat.LIGHT,
        }
        return format_map.get(format.lower(), DiagramFormat.NATIVE)
    
    def _detect_format_from_path(self, path: Path) -> str:
        """Detect format from file path."""
        format_enum = self.format_service.determine_format_from_filename(str(path))
        if format_enum:
            return format_enum.value
        return "native"
    
    async def save_diagram(self, diagram_id: str, content: str, format: str) -> DiagramInfo:
        """Save diagram with specified format."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Get appropriate path for format
            path = self._get_diagram_path(diagram_id, format)
            
            # Ensure parent directory exists
            self.filesystem.mkdir(path.parent, parents=True)
            
            # Validate content matches format
            format_enum = self._format_string_to_enum(format)
            self.format_service.validate_format(content, format_enum)
            
            # Write content
            with self.filesystem.open(path, "wb") as f:
                f.write(content.encode('utf-8'))
            
            # Get file info
            stat = self.filesystem.stat(path)
            
            return DiagramInfo(
                id=diagram_id,
                path=path.relative_to(self.base_path),
                format=format,
                size=stat.size,
                modified=stat.modified,
                created=stat.created
            )
            
        except Exception as e:
            raise StorageError(f"Failed to save diagram {diagram_id}: {e}")
    
    async def load_diagram(self, diagram_id: str) -> tuple[str, str]:
        """Load diagram content and return (content, format)."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Find diagram file
            path = self._get_diagram_path(diagram_id)
            
            if not self.filesystem.exists(path):
                raise StorageError(f"Diagram not found: {diagram_id}")
            
            # Read content
            with self.filesystem.open(path, "rb") as f:
                content = f.read().decode('utf-8')
            
            # Detect format
            format = self._detect_format_from_path(path)
            
            return content, format
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load diagram {diagram_id}: {e}")
    
    async def exists(self, diagram_id: str) -> bool:
        """Check if diagram exists."""
        if not self._initialized:
            await self.initialize()
            
        patterns = self.format_service.construct_search_patterns(diagram_id)
        for pattern in patterns:
            path = self.base_path / pattern
            if self.filesystem.exists(path):
                return True
        return False
    
    async def delete(self, diagram_id: str) -> None:
        """Delete diagram."""
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
        """List all diagrams, optionally filtered by format."""
        if not self._initialized:
            await self.initialize()
            
        diagrams = []
        
        # Define supported extensions
        if format:
            format_enum = self._format_string_to_enum(format)
            extensions = [self.format_service.get_file_extension_for_format(format_enum)]
        else:
            extensions = [".native.json", ".light.yaml", ".readable.yaml"]
        
        # Scan directory recursively for diagram files
        try:
            def scan_directory(dir_path: Path) -> None:
                """Recursively scan directory for diagram files."""
                try:
                    items = self.filesystem.listdir(dir_path)
                except Exception:
                    # Skip directories we can't read
                    return
                    
                for item in items:
                    if item.is_file():
                        # Check if it has a supported extension
                        for ext in extensions:
                            if str(item).endswith(ext):
                                stat = self.filesystem.stat(item)
                                
                                # Get relative path from base
                                rel_path = item.relative_to(self.base_path)
                                
                                # Extract diagram ID including subdirectory
                                diagram_id = str(rel_path.with_suffix(""))
                                if diagram_id.endswith(".native"):
                                    diagram_id = diagram_id[:-7]  # Remove .native
                                elif diagram_id.endswith(".light"):
                                    diagram_id = diagram_id[:-6]   # Remove .light
                                elif diagram_id.endswith(".readable"):
                                    diagram_id = diagram_id[:-9]   # Remove .readable
                                
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
                        # Recursively scan subdirectories
                        scan_directory(item)
            
            scan_directory(self.base_path)
        except Exception as e:
            raise StorageError(f"Failed to list diagrams: {e}")
        
        # Sort by modified time, most recent first
        diagrams.sort(key=lambda x: x.modified, reverse=True)
        return diagrams
    
    async def get_info(self, diagram_id: str) -> DiagramInfo | None:
        """Get diagram metadata without loading content."""
        if not self._initialized:
            await self.initialize()
            
        try:
            path = self._get_diagram_path(diagram_id)
            
            if not self.filesystem.exists(path):
                return None
            
            stat = self.filesystem.stat(path)
            
            return DiagramInfo(
                id=diagram_id,
                path=path.relative_to(self.base_path),
                format=self._detect_format_from_path(path),
                size=stat.size,
                modified=stat.modified,
                created=stat.created
            )
            
        except Exception as e:
            logger.warning(f"Failed to get info for diagram {diagram_id}: {e}")
            return None
    
    async def convert_format(self, diagram_id: str, target_format: str) -> DiagramInfo:
        """Convert diagram to different format."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Load existing diagram
            content, current_format = await self.load_diagram(diagram_id)
            
            # Skip if already in target format
            if current_format == target_format:
                info = await self.get_info(diagram_id)
                if info:
                    return info
                raise StorageError(f"Failed to get info for diagram {diagram_id}")
            
            # Deserialize from current format
            diagram = self.converter.deserialize(content, current_format)
            
            # Serialize to target format
            new_content = self.converter.serialize(diagram, target_format)
            
            # Delete old file
            await self.delete(diagram_id)
            
            # Save with new format
            return await self.save_diagram(diagram_id, new_content, target_format)
            
        except Exception as e:
            raise StorageError(f"Failed to convert diagram {diagram_id} to {target_format}: {e}")