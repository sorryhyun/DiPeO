# Service for handling diagram file I/O operations.

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from dipeo.core.constants import BASE_DIR
from dipeo.core import BaseService, SupportsDiagram

logger = logging.getLogger(__name__)


class FileInfo(BaseModel):
    # Information about a diagram file.
    id: str
    name: str
    path: str
    format: str
    extension: str
    modified: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class DiagramFileRepository(BaseService, SupportsDiagram):
    # Handles file I/O operations for diagram files that implements the SupportsDiagram protocol.
    # Supports reading/writing JSON and YAML files with format detection.
    # Provides file listing and search capabilities.

    def __init__(self, base_dir: Path | None = None):
        super().__init__()
        self.diagrams_dir = (base_dir or BASE_DIR) / "files" / "diagrams"

    async def initialize(self) -> None:
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)

    async def read_file(self, path: str) -> dict[str, Any]:
        file_path = self.diagrams_dir / path

        if not file_path.exists():
            logger.error(
                f"File does not exist: {file_path} (resolved from path: {path}, diagrams_dir: {self.diagrams_dir})"
            )
            raise FileNotFoundError(f"Diagram file not found: {path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        try:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                with file_path.open(encoding="utf-8") as f:
                    try:
                        # First try safe_load
                        return yaml.safe_load(f)
                    except yaml.constructor.ConstructorError as e:
                        # If that fails due to Python objects, try unsafe load and clean up
                        logger.warning(f"YAML file {path} contains Python objects, using unsafe_load: {e}")
                        f.seek(0)
                        data = yaml.unsafe_load(f)
                        # Convert any enum values to strings
                        self._clean_enums(data)
                        return data
            elif file_path.suffix.lower() == ".json":
                with file_path.open(encoding="utf-8") as f:
                    return json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file {path}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise

    async def write_file(self, path: str, content: dict[str, Any]) -> None:
        file_path = self.diagrams_dir / path

        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                with file_path.open("w", encoding="utf-8") as f:
                    yaml.dump(
                        content,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    )
            elif file_path.suffix.lower() == ".json":
                with file_path.open("w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            raise

    async def delete_file(self, path: str) -> None:
        file_path = self.diagrams_dir / path

        if not file_path.exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")

        try:
            file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            raise

    async def list_files(self, directory: str | None = None) -> list[FileInfo]:
        files = []

        if directory:
            scan_dir = self.diagrams_dir / directory
        else:
            scan_dir = self.diagrams_dir

        if not scan_dir.exists():
            return files

        for file_path in scan_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [
                ".yaml",
                ".yml",
                ".json",
            ]:
                try:
                    stats = file_path.stat()
                    relative_path = file_path.relative_to(self.diagrams_dir)

                    format_type = self._determine_format_type(relative_path)

                    # Generate ID that includes subdirectory path (without extension)
                    file_id = str(relative_path.with_suffix(""))

                    file_info = FileInfo(
                        id=file_id,
                        name=file_path.stem,
                        path=str(relative_path),
                        format=format_type,
                        extension=file_path.suffix[1:],
                        modified=datetime.fromtimestamp(
                            stats.st_mtime, tz=UTC
                        ).isoformat(),
                        size=stats.st_size,
                    )

                    files.append(file_info)

                except Exception:
                    # Skip files that can't be processed
                    continue

        files.sort(key=lambda x: x.modified, reverse=True)

        return files

    async def exists(self, path: str) -> bool:
        file_path = self.diagrams_dir / path
        return file_path.exists() and file_path.is_file()

    async def find_by_id(self, diagram_id: str) -> str | None:
        # First check if diagram_id already contains a path separator
        for ext in [".yaml", ".yml", ".json"]:
            path = f"{diagram_id}{ext}"
            full_path = self.diagrams_dir / path
            if await self.exists(path):
                return path

        # Only check subdirectories if diagram_id doesn't contain a path separator
        if "/" not in diagram_id:
            # Then check subdirectories (light, readable, native)
            subdirs = ["light", "readable", "native"]
            for subdir in subdirs:
                for ext in [".yaml", ".yml", ".json"]:
                    path = f"{subdir}/{diagram_id}{ext}"
                    if await self.exists(path):
                        return path

        # Finally, check all files using list_files (for any other subdirectories)
        all_files = await self.list_files()
        for file_info in all_files:
            if file_info.id == diagram_id:
                return file_info.path

        return None

    def _clean_enums(self, data: Any) -> None:
        """Recursively convert enum values to strings in the data structure."""
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(value, 'value'):  # It's an enum
                    data[key] = value.value
                else:
                    self._clean_enums(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if hasattr(item, 'value'):  # It's an enum
                    data[i] = item.value
                else:
                    self._clean_enums(item)
    
    def _determine_format_type(self, relative_path: Path) -> str:
        str(relative_path)

        # Check the first directory in the path
        parts = relative_path.parts
        if len(parts) > 1:
            first_dir = parts[0]
            if first_dir == "native":
                return "native"
            if first_dir == "light":
                return "light"
            if first_dir == "readable":
                return "readable"

        # Default to native for files in root or unknown directories
        return "native"
