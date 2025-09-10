"""Segregated adapter implementations for diagram operations.

These adapters split the monolithic DiagramService functionality into focused,
single-responsibility components following Interface Segregation Principle.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from dipeo.diagram_generated import DiagramFormat, DomainDiagram
from dipeo.domain.base import StorageError
from dipeo.domain.base.mixins import LoggingMixin
from dipeo.domain.base.storage_port import DiagramInfo, FileSystemPort
from dipeo.domain.diagram.segregated_ports import (
    DiagramFilePort,
    DiagramFormatPort,
    DiagramRepositoryPort,
)
from dipeo.domain.diagram.services import DiagramFormatDetector

if TYPE_CHECKING:
    from dipeo.domain.diagram.ports import DiagramStorageSerializer


class FileAdapter(LoggingMixin, DiagramFilePort):
    """Adapter for file I/O operations on diagrams."""

    def __init__(
        self,
        filesystem: FileSystemPort,
        base_path: Path,
        format_port: DiagramFormatPort,
    ):
        """Initialize file adapter.

        Args:
            filesystem: Filesystem abstraction for I/O
            base_path: Base directory for diagram storage
            format_port: Port for format detection and conversion
        """
        self.filesystem = filesystem
        self.base_path = Path(base_path)
        self.format_port = format_port
        self.format_detector = DiagramFormatDetector()

    async def load_from_file(self, file_path: str) -> DomainDiagram:
        """Load a diagram from a file path."""
        path = Path(file_path)

        # Try absolute path first
        if self.filesystem.exists(path):
            with self.filesystem.open(path, "rb") as f:
                content = f.read().decode("utf-8")
            format_enum = self.format_detector.detect_format_from_filename(str(path))
            format_str = format_enum.value if format_enum else None
            return self.format_port.deserialize(content, format_str, str(path))

        # Try relative to base_path
        if not path.is_absolute():
            relative_path = self.base_path / path
            if self.filesystem.exists(relative_path):
                with self.filesystem.open(relative_path, "rb") as f:
                    content = f.read().decode("utf-8")
                format_enum = self.format_detector.detect_format_from_filename(str(relative_path))
                format_str = format_enum.value if format_enum else None
                return self.format_port.deserialize(content, format_str, str(relative_path))

        # Try with various extensions
        patterns = self.format_detector.construct_search_patterns(str(path.stem))
        for pattern in patterns:
            test_path = self.base_path / pattern
            if self.filesystem.exists(test_path):
                with self.filesystem.open(test_path, "rb") as f:
                    content = f.read().decode("utf-8")
                format_str = self._detect_format_from_path(test_path)
                return self.format_port.deserialize(content, format_str, str(test_path))

        raise StorageError(f"Diagram not found: {file_path}")

    async def save_to_file(
        self, diagram: DomainDiagram, file_path: str, format_type: str = "native"
    ) -> None:
        """Save a diagram to a file."""
        path = Path(file_path)

        # Ensure parent directory exists
        self.filesystem.mkdir(path.parent, parents=True)

        # Serialize and save
        content = self.format_port.serialize(diagram, format_type)

        # Write content to file
        with self.filesystem.open(path, "wb") as f:
            f.write(content.encode("utf-8"))

        self.log_debug(f"Saved diagram to {file_path}")

    async def file_exists(self, file_path: str) -> bool:
        """Check if a diagram file exists."""
        path = Path(file_path)

        # Check absolute path
        if self.filesystem.exists(path):
            return True

        # Check relative to base
        if not path.is_absolute():
            if self.filesystem.exists(self.base_path / path):
                return True

        # Check with various extensions
        patterns = self.format_detector.construct_search_patterns(str(path.stem))
        return any(self.filesystem.exists(self.base_path / pattern) for pattern in patterns)

    async def delete_file(self, file_path: str) -> None:
        """Delete a diagram file."""
        path = Path(file_path)

        # Try absolute path first
        if self.filesystem.exists(path):
            self.filesystem.remove(path)
            self.log_debug(f"Deleted file: {file_path}")
            return

        # Try relative to base
        if not path.is_absolute():
            relative_path = self.base_path / path
            if self.filesystem.exists(relative_path):
                self.filesystem.remove(relative_path)
                self.log_debug(f"Deleted file: {relative_path}")
                return

        raise StorageError(f"File not found: {file_path}")

    def _detect_format_from_path(self, path: Path) -> str:
        """Detect format from file path."""
        format_enum = self.format_detector.detect_format_from_filename(str(path))
        if format_enum:
            return format_enum.value
        return "native"


class FormatAdapter(LoggingMixin, DiagramFormatPort):
    """Adapter for diagram format detection and conversion."""

    def __init__(self, serializer: "DiagramStorageSerializer"):
        """Initialize format adapter.

        Args:
            serializer: Serializer for format conversion
        """
        self.serializer = serializer
        self.format_detector = DiagramFormatDetector()

    def detect_format(self, content: str) -> DiagramFormat:
        """Detect the format of diagram content."""
        import json

        import yaml

        try:
            data = json.loads(content)
            if "nodes" in data and "arrows" in data:
                return DiagramFormat.NATIVE
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(content)
                if data and isinstance(data, dict):
                    if "format" in data and data["format"] == "light":
                        return DiagramFormat.LIGHT
                    elif "version" in data and data["version"] == "readable":
                        return DiagramFormat.READABLE
            except yaml.YAMLError:
                pass
        return DiagramFormat.NATIVE  # Default

    def serialize(self, diagram: DomainDiagram, format_type: str) -> str:
        """Serialize a diagram to a specific format."""
        return self.serializer.serialize_for_storage(diagram, format_type)

    def deserialize(
        self, content: str, format_type: str | None = None, diagram_path: str | None = None
    ) -> DomainDiagram:
        """Deserialize string content to a domain diagram."""
        return self.serializer.deserialize_from_storage(content, format_type, diagram_path)

    def convert_format(self, diagram: DomainDiagram, from_format: str, to_format: str) -> str:
        """Convert a diagram from one format to another."""
        # First ensure we have the diagram in domain form
        # (it already is, since input is DomainDiagram)
        # Then serialize to target format
        return self.serialize(diagram, to_format)


class RepositoryAdapter(LoggingMixin, DiagramRepositoryPort):
    """Adapter for diagram CRUD and query operations."""

    def __init__(
        self,
        filesystem: FileSystemPort,
        base_path: Path,
        format_port: DiagramFormatPort,
    ):
        """Initialize repository adapter.

        Args:
            filesystem: Filesystem abstraction for I/O
            base_path: Base directory for diagram storage
            format_port: Port for format operations
        """
        self.filesystem = filesystem
        self.base_path = Path(base_path)
        self.format_port = format_port
        self.format_detector = DiagramFormatDetector()

    async def create(self, name: str, diagram: DomainDiagram, format_type: str = "native") -> str:
        """Create a new diagram with a unique ID."""
        # Map format string to enum
        if format_type == "native" or format_type == "json":
            diagram_format = DiagramFormat.NATIVE
        elif format_type == "readable":
            diagram_format = DiagramFormat.READABLE
        elif format_type == "light":
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
        content = self.format_port.serialize(diagram, diagram_format.value)
        path = self._get_diagram_path(diagram_id, diagram_format.value)

        # Ensure parent directory exists
        self.filesystem.mkdir(path.parent, parents=True)

        # Write content to file
        with self.filesystem.open(path, "wb") as f:
            f.write(content.encode("utf-8"))

        self.log_debug(f"Created diagram: {diagram_id}")
        return diagram_id

    async def get(self, diagram_id: str) -> Optional[DomainDiagram]:
        """Retrieve a diagram by its ID."""
        try:
            # Find the diagram file
            path = self._get_diagram_path(diagram_id)
            if not self.filesystem.exists(path):
                return None

            # Load and deserialize
            with self.filesystem.open(path, "rb") as f:
                content = f.read().decode("utf-8")

            format_str = self._detect_format_from_path(path)
            diagram = self.format_port.deserialize(content, format_str)

            # Ensure metadata.id is set
            if diagram and diagram.metadata:
                diagram.metadata.id = diagram_id
                if not diagram.metadata.name:
                    diagram.metadata.name = diagram_id.split("/")[-1]

            return diagram
        except Exception as e:
            self.log_warning(f"Failed to get diagram {diagram_id}: {e}")
            return None

    async def update(self, diagram_id: str, diagram: DomainDiagram) -> None:
        """Update an existing diagram."""
        if not await self.exists(diagram_id):
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")

        # Get existing path and format
        path = self._get_diagram_path(diagram_id)
        if not self.filesystem.exists(path):
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")

        format_str = self._detect_format_from_path(path)
        content = self.format_port.serialize(diagram, format_str)

        # Write updated content
        with self.filesystem.open(path, "wb") as f:
            f.write(content.encode("utf-8"))

        self.log_debug(f"Updated diagram: {diagram_id}")

    async def delete(self, diagram_id: str) -> None:
        """Delete a diagram from storage."""
        # Find and delete the file
        path = self._get_diagram_path(diagram_id)
        if not self.filesystem.exists(path):
            raise StorageError(f"Diagram not found: {diagram_id}")

        self.filesystem.remove(path)
        self.log_debug(f"Deleted diagram: {diagram_id}")

    async def exists(self, diagram_id: str) -> bool:
        """Check if a diagram exists."""
        # Check various possible extensions
        patterns = self.format_detector.construct_search_patterns(diagram_id)
        for pattern in patterns:
            path = self.base_path / pattern
            if self.filesystem.exists(path):
                return True

        # Also check projects directory
        projects_path = self.base_path.parent / "projects"
        if self.filesystem.exists(projects_path):
            for pattern in patterns:
                path = projects_path / pattern
                if self.filesystem.exists(path):
                    return True

        return False

    async def list(self, format_type: str | None = None) -> list[DiagramInfo]:
        """List all diagrams, optionally filtered by format."""
        diagrams = []

        if format_type:
            format_enum = self._format_string_to_enum(format_type)
            extensions = [self.format_detector.get_file_extension(format_enum)]
        else:
            extensions = [
                ".native.json",
                ".light.yaml",
                ".light.yml",
                ".readable.yaml",
                ".readable.yml",
            ]

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
                            # Calculate relative path
                            root_base = self.base_path.parent
                            rel_path = item.relative_to(root_base)
                            diagram_id = str(rel_path).replace("\\", "/")

                            diagrams.append(
                                DiagramInfo(
                                    id=diagram_id,
                                    path=rel_path,
                                    format=self._detect_format_from_path(item),
                                    size=stat.size,
                                    modified=stat.modified,
                                    created=stat.created,
                                )
                            )
                            break
                elif item.is_dir():
                    scan_directory(item, base_for_relative)

        # Scan both files/ and projects/ directories
        self.log_debug(f"Scanning files directory: {self.base_path}")
        scan_directory(self.base_path, self.base_path)

        # Also scan projects/ directory if it exists
        projects_path = self.base_path.parent / "projects"
        if self.filesystem.exists(projects_path):
            self.log_debug(f"Scanning projects directory: {projects_path}")
            scan_directory(projects_path, projects_path)

        self.log_info(f"Found {len(diagrams)} diagrams total")
        diagrams.sort(key=lambda x: x.modified, reverse=True)
        return diagrams

    def _get_diagram_path(self, diagram_id: str, format: str | None = None) -> Path:
        """Get the path for a diagram, handling various extensions and formats."""
        supported_extensions = [
            ".native.json",
            ".light.yaml",
            ".light.yml",
            ".readable.yaml",
            ".readable.yml",
            ".json",
            ".yaml",
            ".yml",
        ]

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

    def _format_string_to_enum(self, format_str: str) -> DiagramFormat:
        """Convert format string to enum."""
        format_map = {
            "native": DiagramFormat.NATIVE,
            "light": DiagramFormat.LIGHT,
            "readable": DiagramFormat.READABLE,
            "json": DiagramFormat.NATIVE,
            "yaml": DiagramFormat.LIGHT,
        }
        return format_map.get(format_str.lower(), DiagramFormat.NATIVE)
