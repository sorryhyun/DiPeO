"""Service for handling diagram file I/O operations."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dipeo_core import BaseService

from config import BASE_DIR

from .models import FileInfo

logger = logging.getLogger(__name__)


# FileInfo is now imported from models.py


class DiagramStorageService(BaseService):
    """Handles file I/O operations for diagram files."""

    def __init__(self, base_dir: Optional[Path] = None):
        super().__init__()
        self.diagrams_dir = (base_dir or BASE_DIR) / "files" / "diagrams"
        logger.info(f"DiagramStorageService initialized with dir: {self.diagrams_dir}")

    async def initialize(self) -> None:
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured diagrams directory exists: {self.diagrams_dir}")

    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read a diagram file and return its contents as a dictionary."""
        file_path = self.diagrams_dir / path
        logger.debug(f"Attempting to read file: {file_path}")

        if not file_path.exists():
            logger.error(f"File does not exist: {file_path} (resolved from path: {path}, diagrams_dir: {self.diagrams_dir})")
            raise FileNotFoundError(f"Diagram file not found: {path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        try:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                with file_path.open(encoding="utf-8") as f:
                    return yaml.safe_load(f)
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

    async def write_file(self, path: str, content: Dict[str, Any]) -> None:
        """Write a dictionary to a diagram file."""
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

            logger.info(f"Successfully wrote file: {path}")

        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            raise

    async def delete_file(self, path: str) -> None:
        """Delete a diagram file."""
        file_path = self.diagrams_dir / path

        if not file_path.exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")

        try:
            file_path.unlink()
            logger.info(f"Successfully deleted file: {path}")
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            raise

    async def list_files(
        self, directory: Optional[str] = None
    ) -> List[FileInfo]:
        """List all diagram files in the diagrams directory."""
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

                    file_info = FileInfo(
                        id=file_path.stem,
                        name=file_path.stem.replace("_", " ").replace("-", " ").title(),
                        path=str(relative_path),
                        format=format_type,
                        extension=file_path.suffix[1:],
                        modified=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat(),
                        size=stats.st_size,
                    )

                    files.append(file_info)

                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")
                    continue

        files.sort(key=lambda x: x.modified, reverse=True)

        return files

    async def exists(self, path: str) -> bool:
        """Check if a diagram file exists."""
        file_path = self.diagrams_dir / path
        return file_path.exists() and file_path.is_file()

    async def find_by_id(self, diagram_id: str) -> Optional[str]:
        """Find a diagram file by its ID (filename without extension)."""
        for ext in [".yaml", ".yml", ".json"]:
            path = f"{diagram_id}{ext}"
            if await self.exists(path):
                return path

        for file_info in await self.list_files():
            if file_info.id == diagram_id:
                return file_info.path

        return None

    def _determine_format_type(self, relative_path: Path) -> str:
        path_str = str(relative_path)

        if "readable" in path_str:
            return "readable"
        if relative_path.parent == Path():
            return "light"
        return "native"
