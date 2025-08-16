"""Main diagram service - single source of truth for all diagram operations."""

import logging
from pathlib import Path
from datetime import datetime

from dipeo.core import BaseService, StorageError
from dipeo.core.ports.diagram_port import DiagramPort
from dipeo.domain.ports.storage import DiagramInfo, FileSystemPort
from dipeo.domain.diagram.services import DiagramFormatDetector
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.diagram_generated import DiagramFormat, DomainDiagram
from .converter_service import DiagramConverterService
from .compilation_service import CompilationService

logger = logging.getLogger(__name__)


class DiagramService(BaseService, DiagramPort):
    """Single source of truth for all diagram operations.
    
    This service provides:
    - CRUD operations (create, get, update, delete)
    - Loading operations (from file or string)
    - Format operations (detect, serialize/deserialize)
    - Compilation (compile to ExecutableDiagram)
    - Query operations (exists, list)
    - Direct filesystem storage operations
    """
    
    def __init__(
        self,
        filesystem: FileSystemPort,
        base_path: str | Path,
        converter: DiagramConverterService | None = None,
        compiler: CompilationService | None = None
    ):
        super().__init__()
        self.filesystem = filesystem
        self.base_path = Path(base_path)
        self.converter = converter or DiagramConverterService()
        self.compiler = compiler or CompilationService()
        self.format_detector = DiagramFormatDetector()
        self._initialized = False
    
    async def initialize(self) -> None:
        if self._initialized:
            return
            
        try:
            self.filesystem.mkdir(self.base_path, parents=True)
        except Exception as e:
            raise StorageError(f"Failed to initialize diagram storage: {e}")
            
        await self.converter.initialize()
        await self.compiler.initialize()
        
        self._initialized = True

    
    def detect_format(self, content: str) -> DiagramFormat:
        """Detect the format of diagram content."""
        format_id = self.converter.detect_format(content)
        if not format_id:
            raise ValueError("Unable to detect diagram format")
        
        return self._format_string_to_enum(format_id)
    
    def serialize(self, diagram: DomainDiagram, format_type: str) -> str:
        """Serialize a DomainDiagram to string."""
        return self.converter.serialize_for_storage(diagram, format_type)
    
    def deserialize(self, content: str, format_type: str | None = None) -> DomainDiagram:
        """Deserialize string content to DomainDiagram."""
        return self.converter.deserialize_from_storage(content, format_type)

    
    async def load_from_file(self, file_path: str) -> DomainDiagram:
        """Load a diagram from a file path."""
        if not self._initialized:
            await self.initialize()
            
        path = Path(file_path)
        
        # Try absolute path first
        if self.filesystem.exists(path):
            with self.filesystem.open(path, "rb") as f:
                content = f.read().decode('utf-8')
            format_enum = self.format_detector.detect_format_from_filename(str(path))
            format_str = format_enum.value if format_enum else None
            return self.deserialize(content, format_str)
        
        # Try relative to base_path
        if not path.is_absolute():
            relative_path = self.base_path / path
            if self.filesystem.exists(relative_path):
                with self.filesystem.open(relative_path, "rb") as f:
                    content = f.read().decode('utf-8')
                format_enum = self.format_detector.detect_format_from_filename(str(relative_path))
                format_str = format_enum.value if format_enum else None
                return self.deserialize(content, format_str)
        
        # Extract diagram ID and try with various extensions
        if "files" in path.parts:
            idx = path.parts.index("files")
            rel_path = Path(*path.parts[idx+1:])
        elif "projects" in path.parts:
            idx = path.parts.index("projects")
            rel_path = Path("projects", *path.parts[idx+1:])
        else:
            rel_path = path
        
        diagram_id = str(rel_path.with_suffix(""))
        
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        # Try to find with path resolution
        resolved_path = self._get_diagram_path(diagram_id)
        if self.filesystem.exists(resolved_path):
            with self.filesystem.open(resolved_path, "rb") as f:
                content = f.read().decode('utf-8')
            format_str = self._detect_format_from_path(resolved_path)
            return self.deserialize(content, format_str)
        
        raise StorageError(f"Diagram not found: {file_path}")
    
    def load_from_string(self, content: str, format_type: str | None = None) -> DomainDiagram:
        """Load a diagram from string content."""
        return self.deserialize(content, format_type)
    
    async def list_diagrams(self, format_type: str | None = None) -> list[DiagramInfo]:
        """List all diagrams, optionally filtered by format."""
        if not self._initialized:
            await self.initialize()
            
        diagrams = []
        
        if format_type:
            format_enum = self._format_string_to_enum(format_type)
            extensions = [self.format_detector.get_file_extension(format_enum)]
        else:
            extensions = [".native.json", ".light.yaml", ".light.yml", ".readable.yaml", ".readable.yml"]
        
        try:
            def scan_directory(dir_path: Path, base_for_relative: Path) -> None:
                try:
                    items = self.filesystem.listdir(dir_path)
                except Exception:
                    return
                    
                for item in items:
                    if item.is_file():
                        for ext in extensions:
                            if str(item).endswith(ext):
                                stat = self.filesystem.stat(item)
                                # Calculate relative path from the root (parent of files/projects)
                                root_base = self.base_path.parent
                                rel_path = item.relative_to(root_base)
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
                        scan_directory(item, base_for_relative)
            
            # Scan both files/ and projects/ directories
            logger.debug(f"Scanning files directory: {self.base_path}")
            scan_directory(self.base_path, self.base_path)
            
            # Also scan projects/ directory if it exists
            projects_path = self.base_path.parent / "projects"
            if self.filesystem.exists(projects_path):
                logger.debug(f"Scanning projects directory: {projects_path}")
                scan_directory(projects_path, projects_path)
            else:
                logger.debug(f"Projects directory not found: {projects_path}")
                
        except Exception as e:
            raise StorageError(f"Failed to list diagrams: {e}")
        
        logger.info(f"Found {len(diagrams)} diagrams total")
        diagrams.sort(key=lambda x: x.modified, reverse=True)
        return diagrams
    
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
        
        # Generate unique diagram ID
        diagram_id = name
        counter = 1
        while await self.exists(diagram_id):
            diagram_id = f"{name}_{counter}"
            counter += 1
        
        # Serialize and save
        content = self.converter.serialize_for_storage(diagram, diagram_format.value)
        path = self._get_diagram_path(diagram_id, diagram_format.value)
        
        # Ensure parent directory exists
        self.filesystem.mkdir(path.parent, parents=True)
        
        # Write content to file
        with self.filesystem.open(path, "wb") as f:
            f.write(content.encode('utf-8'))
        
        return diagram_id
    
    async def update_diagram(self, diagram_id: str, diagram: DomainDiagram) -> None:
        if not self._initialized:
            await self.initialize()
            
        if not await self.exists(diagram_id):
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")
        
        # Get existing path and format
        path = self._get_diagram_path(diagram_id)
        if not self.filesystem.exists(path):
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")
        
        format_str = self._detect_format_from_path(path)
        content = self.converter.serialize_for_storage(diagram, format_str)
        
        # Write updated content
        with self.filesystem.open(path, "wb") as f:
            f.write(content.encode('utf-8'))
    
    
    async def delete_diagram(self, path: str) -> None:
        if not self._initialized:
            await self.initialize()
            
        path_obj = Path(path)
        diagram_id = path_obj.stem
        
        for suffix in [".native", ".light", ".readable"]:
            if diagram_id.endswith(suffix):
                diagram_id = diagram_id[:-len(suffix)]
                break
        
        # Find and delete the file
        resolved_path = self._get_diagram_path(diagram_id)
        if not self.filesystem.exists(resolved_path):
            raise StorageError(f"Diagram not found: {diagram_id}")
        
        self.filesystem.remove(resolved_path)
        logger.debug(f"Deleted diagram: {diagram_id}")
    
    
    async def get_diagram(self, diagram_id: str) -> DomainDiagram | None:
        """Get diagram by its ID.
        
        Returns:
            DomainDiagram if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Find the diagram file
            path = self._get_diagram_path(diagram_id)
            if not self.filesystem.exists(path):
                return None
            
            # Load and deserialize
            with self.filesystem.open(path, "rb") as f:
                content = f.read().decode('utf-8')
            
            format_str = self._detect_format_from_path(path)
            diagram = self.converter.deserialize_from_storage(content, format_str)
            
            # Ensure metadata.id is set to the diagram_id
            if diagram:
                if diagram.metadata is None:
                    from dipeo.diagram_generated import DiagramMetadata
                    from datetime import datetime
                    # Get file stats for created/modified times
                    try:
                        stat = self.filesystem.stat(path)
                        created_time = stat.created.isoformat() if hasattr(stat, 'created') else datetime.now().isoformat()
                        modified_time = stat.modified.isoformat() if hasattr(stat, 'modified') else datetime.now().isoformat()
                    except:
                        created_time = datetime.now().isoformat()
                        modified_time = datetime.now().isoformat()
                    
                    diagram.metadata = DiagramMetadata(
                        version="1.0.0",
                        created=created_time,
                        modified=modified_time
                    )
                diagram.metadata.id = diagram_id
                if not diagram.metadata.name:
                    # Extract name from the last part of the path
                    name_parts = diagram_id.split('/')
                    diagram.metadata.name = name_parts[-1] if name_parts else diagram_id
            
            return diagram
        except Exception as e:
            logger.warning(f"Failed to get diagram {diagram_id}: {e}")
            return None
    
    
    async def exists(self, diagram_id: str) -> bool:
        """Check if a diagram exists."""
        if not self._initialized:
            await self.initialize()
            
        # Check various possible extensions
        supported_extensions = [".native.json", ".light.yaml", ".light.yml", 
                              ".readable.yaml", ".readable.yml", ".json", ".yaml", ".yml"]
        
        # If diagram_id already has an extension, check directly
        for ext in supported_extensions:
            if diagram_id.endswith(ext):
                path = self.base_path / diagram_id
                return self.filesystem.exists(path)
        
        # Otherwise, try to find with various patterns
        patterns = self.format_detector.construct_search_patterns(diagram_id)
        for pattern in patterns:
            path = self.base_path / pattern
            if self.filesystem.exists(path):
                return True
        
        return False
    
    # Compilation methods
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile a DomainDiagram to ExecutableDiagram.
        
        Args:
            domain_diagram: The diagram to compile
            
        Returns:
            ExecutableDiagram: The compiled diagram ready for execution
        """
        return self.compiler.compile(domain_diagram)
    
    
    def _format_string_to_enum(self, format_str: str) -> DiagramFormat:
        format_map = {
            "native": DiagramFormat.NATIVE,
            "light": DiagramFormat.LIGHT,
            "readable": DiagramFormat.READABLE,
            "json": DiagramFormat.NATIVE,
            "yaml": DiagramFormat.LIGHT,
        }
        return format_map.get(format_str.lower(), DiagramFormat.NATIVE)
    
    def _get_diagram_path(self, diagram_id: str, format: str | None = None) -> Path:
        """Get the path for a diagram, handling various extensions and formats."""
        supported_extensions = [".native.json", ".light.yaml", ".light.yml", 
                              ".readable.yaml", ".readable.yml", ".json", ".yaml", ".yml"]
        
        # List of directories to search in order
        search_dirs = [self.base_path]  # files/ directory
        projects_path = self.base_path.parent / "projects"
        if self.filesystem.exists(projects_path):
            search_dirs.append(projects_path)
        
        # If diagram_id starts with "projects/" or "files/", use it directly
        if diagram_id.startswith("projects/") or diagram_id.startswith("files/"):
            root_base = self.base_path.parent
            full_path = root_base / diagram_id
            if self.filesystem.exists(full_path):
                return full_path
            # Also try with extensions
            for ext in supported_extensions:
                if not diagram_id.endswith(ext):
                    test_path = root_base / f"{diagram_id}{ext}"
                    if self.filesystem.exists(test_path):
                        return test_path
        
        # Check if diagram_id already has an extension
        for ext in supported_extensions:
            if diagram_id.endswith(ext):
                for search_dir in search_dirs:
                    path = search_dir / diagram_id
                    if self.filesystem.exists(path):
                        return path
                # Return first search dir path if none exist (for creation)
                return search_dirs[0] / diagram_id
        
        # If format is specified, use it
        if format:
            format_enum = self._format_string_to_enum(format)
            extension = self.format_detector.get_file_extension(format_enum)
            # Check all search dirs
            for search_dir in search_dirs:
                path = search_dir / f"{diagram_id}{extension}"
                if self.filesystem.exists(path):
                    return path
            # Return first search dir path if none exist (for creation)
            return search_dirs[0] / f"{diagram_id}{extension}"
        
        # Try to find existing file with various extensions
        patterns = self.format_detector.construct_search_patterns(diagram_id)
        for pattern in patterns:
            for search_dir in search_dirs:
                path = search_dir / pattern
                if self.filesystem.exists(path):
                    return path
        
        # Default to native format in files/ directory
        return self.base_path / f"{diagram_id}.native.json"
    
    def _detect_format_from_path(self, path: Path) -> str:
        """Detect format from file path."""
        format_enum = self.format_detector.detect_format_from_filename(str(path))
        if format_enum:
            return format_enum.value
        return "native"