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
        self.filesystem = filesystem
        self.base_path = Path(base_path)
        self.format_port = format_port
        self.format_detector = DiagramFormatDetector()

    async def load_from_file(self, file_path: str) -> DomainDiagram:
        path = Path(file_path)
        self.log_debug(f"[FileAdapter] load_from_file called with: {file_path}")

        if self.filesystem.exists(path):
            self.log_debug(f"[FileAdapter] Found file at exact path: {path}")
            with self.filesystem.open(path, "rb") as f:
                content = f.read().decode("utf-8")
            format_enum = self.format_detector.detect_format_from_filename(str(path))
            format_str = format_enum.value if format_enum else None
            self.log_debug(f"[FileAdapter] Calling deserialize with diagram_path: {path!s}")
            return self.format_port.deserialize(content, format_str, str(path))

        if not path.is_absolute():
            relative_path = self.base_path / path
            self.log_debug(f"[FileAdapter] Checking relative path: {relative_path}")
            if self.filesystem.exists(relative_path):
                self.log_debug(f"[FileAdapter] Found file at relative path: {relative_path}")
                with self.filesystem.open(relative_path, "rb") as f:
                    content = f.read().decode("utf-8")
                format_enum = self.format_detector.detect_format_from_filename(str(relative_path))
                format_str = format_enum.value if format_enum else None
                self.log_debug(
                    f"[FileAdapter] Calling deserialize with diagram_path: {relative_path!s}"
                )
                return self.format_port.deserialize(content, format_str, str(relative_path))

        self.log_debug(f"[FileAdapter] Trying search patterns for: {path.stem}")
        patterns = self.format_detector.construct_search_patterns(str(path.stem))
        for pattern in patterns:
            test_path = self.base_path / pattern
            self.log_debug(f"[FileAdapter] Checking pattern: {test_path}")
            if self.filesystem.exists(test_path):
                self.log_debug(f"[FileAdapter] Found file at pattern: {test_path}")
                with self.filesystem.open(test_path, "rb") as f:
                    content = f.read().decode("utf-8")
                format_str = self._detect_format_from_path(test_path)
                self.log_debug(
                    f"[FileAdapter] Calling deserialize with diagram_path: {test_path!s}"
                )
                return self.format_port.deserialize(content, format_str, str(test_path))

        raise StorageError(f"Diagram not found: {file_path}")

    async def save_to_file(
        self, diagram: DomainDiagram, file_path: str, format_type: str = "native"
    ) -> None:
        path = Path(file_path)

        self.filesystem.mkdir(path.parent, parents=True)
        content = self.format_port.serialize(diagram, format_type)

        with self.filesystem.open(path, "wb") as f:
            f.write(content.encode("utf-8"))

        self.log_debug(f"Saved diagram to {file_path}")

    async def file_exists(self, file_path: str) -> bool:
        path = Path(file_path)

        if self.filesystem.exists(path):
            return True

        if not path.is_absolute():
            if self.filesystem.exists(self.base_path / path):
                return True

        patterns = self.format_detector.construct_search_patterns(str(path.stem))
        return any(self.filesystem.exists(self.base_path / pattern) for pattern in patterns)

    async def delete_file(self, file_path: str) -> None:
        path = Path(file_path)

        if self.filesystem.exists(path):
            self.filesystem.remove(path)
            self.log_debug(f"Deleted file: {file_path}")
            return

        if not path.is_absolute():
            relative_path = self.base_path / path
            if self.filesystem.exists(relative_path):
                self.filesystem.remove(relative_path)
                self.log_debug(f"Deleted file: {relative_path}")
                return

        raise StorageError(f"File not found: {file_path}")

    def _detect_format_from_path(self, path: Path) -> str:
        format_enum = self.format_detector.detect_format_from_filename(str(path))
        if format_enum:
            return format_enum.value
        return "native"


class FormatAdapter(LoggingMixin, DiagramFormatPort):
    """Adapter for diagram format detection and conversion."""

    def __init__(self, serializer: "DiagramStorageSerializer"):
        self.serializer = serializer
        self.format_detector = DiagramFormatDetector()

    def detect_format(self, content: str) -> DiagramFormat:
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
        return DiagramFormat.NATIVE

    def serialize(self, diagram: DomainDiagram, format_type: str) -> str:
        return self.serializer.serialize_for_storage(diagram, format_type)

    def deserialize(
        self, content: str, format_type: str | None = None, diagram_path: str | None = None
    ) -> DomainDiagram:
        self.log_debug(f"[FormatAdapter] deserialize called with diagram_path: {diagram_path}")
        return self.serializer.deserialize_from_storage(content, format_type, diagram_path)

    def convert_format(self, diagram: DomainDiagram, from_format: str, to_format: str) -> str:
        return self.serialize(diagram, to_format)


class RepositoryAdapter(LoggingMixin, DiagramRepositoryPort):
    """Adapter for diagram CRUD and query operations."""

    def __init__(
        self,
        filesystem: FileSystemPort,
        base_path: Path,
        format_port: DiagramFormatPort,
    ):
        self.filesystem = filesystem
        self.base_path = Path(base_path)
        self.format_port = format_port
        self.format_detector = DiagramFormatDetector()

    async def create(self, name: str, diagram: DomainDiagram, format_type: str = "native") -> str:
        if format_type == "native" or format_type == "json":
            diagram_format = DiagramFormat.NATIVE
        elif format_type == "readable":
            diagram_format = DiagramFormat.READABLE
        elif format_type == "light":
            diagram_format = DiagramFormat.LIGHT
        else:
            diagram_format = DiagramFormat.NATIVE

        diagram_id = name
        counter = 1
        while await self.exists(diagram_id):
            diagram_id = f"{name}_{counter}"
            counter += 1

        content = self.format_port.serialize(diagram, diagram_format.value)
        path = self._get_diagram_path(diagram_id, diagram_format.value)

        self.filesystem.mkdir(path.parent, parents=True)

        with self.filesystem.open(path, "wb") as f:
            f.write(content.encode("utf-8"))

        self.log_debug(f"Created diagram: {diagram_id}")
        return diagram_id

    async def get(self, diagram_id: str) -> Optional[DomainDiagram]:
        try:
            path = self._get_diagram_path(diagram_id)
            if not self.filesystem.exists(path):
                return None

            with self.filesystem.open(path, "rb") as f:
                content = f.read().decode("utf-8")

            format_str = self._detect_format_from_path(path)
            diagram = self.format_port.deserialize(content, format_str)

            if diagram:
                # Ensure metadata exists
                if not diagram.metadata:
                    from dipeo.diagram_generated import DiagramMetadata

                    diagram.metadata = DiagramMetadata(
                        id=diagram_id,
                        name=diagram_id.split("/")[-1],
                        version="1.0",
                        created="",
                        modified="",
                    )
                else:
                    # Update existing metadata
                    diagram.metadata.id = diagram_id
                    if not diagram.metadata.name:
                        diagram.metadata.name = diagram_id.split("/")[-1]

            return diagram
        except Exception as e:
            # Log warning with more detail about what kind of error occurred
            import pydantic

            if isinstance(e, pydantic.ValidationError):
                self.log_warning(
                    f"Failed to validate diagram {diagram_id}: {e.error_count()} validation errors"
                )
                for error in e.errors()[:3]:  # Show first 3 errors
                    self.log_debug(f"  - {error['loc']}: {error['msg']}")
            else:
                self.log_warning(f"Failed to get diagram {diagram_id}: {e}")

            # Re-raise the exception so the caller can handle it
            # This allows the resolver to create a minimal diagram with error info
            raise

    async def update(self, diagram_id: str, diagram: DomainDiagram) -> None:
        if not await self.exists(diagram_id):
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")

        path = self._get_diagram_path(diagram_id)
        if not self.filesystem.exists(path):
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")

        format_str = self._detect_format_from_path(path)
        content = self.format_port.serialize(diagram, format_str)

        with self.filesystem.open(path, "wb") as f:
            f.write(content.encode("utf-8"))

        self.log_debug(f"Updated diagram: {diagram_id}")

    async def delete(self, diagram_id: str) -> None:
        path = self._get_diagram_path(diagram_id)
        if not self.filesystem.exists(path):
            raise StorageError(f"Diagram not found: {diagram_id}")

        self.filesystem.remove(path)
        self.log_debug(f"Deleted diagram: {diagram_id}")

    async def exists(self, diagram_id: str) -> bool:
        patterns = self.format_detector.construct_search_patterns(diagram_id)
        for pattern in patterns:
            path = self.base_path / pattern
            if self.filesystem.exists(path):
                return True

        projects_path = self.base_path.parent / "projects"
        if self.filesystem.exists(projects_path):
            for pattern in patterns:
                path = projects_path / pattern
                if self.filesystem.exists(path):
                    return True

        examples_path = self.base_path.parent / "examples"
        if self.filesystem.exists(examples_path):
            for pattern in patterns:
                path = examples_path / pattern
                if self.filesystem.exists(path):
                    return True

        return False

    async def list(self, format_type: str | None = None) -> list[DiagramInfo]:
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
                    # Skip the claude_code directory when scanning projects
                    # Convert to string path and check if it contains the pattern
                    item_str = str(item).replace("\\", "/")
                    if "/projects/claude_code" in item_str:
                        continue
                    scan_directory(item, base_for_relative)

        self.log_debug(f"Scanning files directory: {self.base_path}")
        scan_directory(self.base_path, self.base_path)

        projects_path = self.base_path.parent / "projects"
        if self.filesystem.exists(projects_path):
            self.log_debug(f"Scanning projects directory: {projects_path}")
            scan_directory(projects_path, projects_path)

        examples_path = self.base_path.parent / "examples"
        if self.filesystem.exists(examples_path):
            self.log_debug(f"Scanning examples directory: {examples_path}")
            scan_directory(examples_path, examples_path)

        self.log_info(f"Found {len(diagrams)} diagrams total")
        diagrams.sort(key=lambda x: x.modified, reverse=True)
        return diagrams

    def _get_diagram_path(self, diagram_id: str, format: str | None = None) -> Path:
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

        search_dirs = [self.base_path]
        projects_path = self.base_path.parent / "projects"
        if self.filesystem.exists(projects_path):
            search_dirs.append(projects_path)
        examples_path = self.base_path.parent / "examples"
        if self.filesystem.exists(examples_path):
            search_dirs.append(examples_path)

        if (
            diagram_id.startswith("projects/")
            or diagram_id.startswith("files/")
            or diagram_id.startswith("examples/")
        ):
            root_base = self.base_path.parent
            full_path = root_base / diagram_id
            if self.filesystem.exists(full_path):
                return full_path
            for ext in supported_extensions:
                if not diagram_id.endswith(ext):
                    test_path = root_base / f"{diagram_id}{ext}"
                    if self.filesystem.exists(test_path):
                        return test_path

        for ext in supported_extensions:
            if diagram_id.endswith(ext):
                for search_dir in search_dirs:
                    path = search_dir / diagram_id
                    if self.filesystem.exists(path):
                        return path
                return search_dirs[0] / diagram_id

        if format:
            format_enum = self._format_string_to_enum(format)
            extension = self.format_detector.get_file_extension(format_enum)
            for search_dir in search_dirs:
                path = search_dir / f"{diagram_id}{extension}"
                if self.filesystem.exists(path):
                    return path
            return search_dirs[0] / f"{diagram_id}{extension}"

        patterns = self.format_detector.construct_search_patterns(diagram_id)
        for pattern in patterns:
            for search_dir in search_dirs:
                path = search_dir / pattern
                if self.filesystem.exists(path):
                    return path

        return self.base_path / f"{diagram_id}.native.json"

    def _detect_format_from_path(self, path: Path) -> str:
        format_enum = self.format_detector.detect_format_from_filename(str(path))
        if format_enum:
            return format_enum.value
        return "native"

    def _format_string_to_enum(self, format_str: str) -> DiagramFormat:
        format_map = {
            "native": DiagramFormat.NATIVE,
            "light": DiagramFormat.LIGHT,
            "readable": DiagramFormat.READABLE,
            "json": DiagramFormat.NATIVE,
            "yaml": DiagramFormat.LIGHT,
        }
        return format_map.get(format_str.lower(), DiagramFormat.NATIVE)
