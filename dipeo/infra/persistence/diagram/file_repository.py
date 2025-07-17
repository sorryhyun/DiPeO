"""File repository for diagram persistence."""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from dipeo.core.constants import BASE_DIR
from dipeo.domain.diagram.services import DiagramBusinessLogic as DiagramDomainService

logger = logging.getLogger(__name__)


class DiagramFileRepository:
    # File-based repository for diagram storage

    def __init__(self, domain_service: DiagramDomainService, base_dir: str = None):
        # Initialize the repository
        self.domain_service = domain_service
        self.base_dir = Path(base_dir) if base_dir else Path(BASE_DIR)
        self.diagrams_dir = self.base_dir / "files" / "diagrams"

    async def initialize(self) -> None:
        # Initialize the repository by ensuring directories exist
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)

    async def find_by_id(self, diagram_id: str) -> str | None:
        """Find a diagram file by ID."""
        # Construct possible paths for the diagram
        search_paths = self.domain_service.construct_search_paths(
            diagram_id,
            base_extensions=[".yaml", ".yml", ".json"]
        )

        for path in search_paths:
            file_path = self.diagrams_dir / path
            if file_path.exists():
                return path

        # If not found in standard locations, scan all files
        all_files = await self.list_files()
        for file_info in all_files:
            try:
                data = await self.read_file(file_info["path"])
                if data.get("id") == diagram_id:
                    return file_info["path"]
            except Exception:
                continue

        return None

    async def read_file(self, path: str) -> dict[str, Any]:
        """Read a diagram file and return parsed content."""
        file_path = self.diagrams_dir / path
        if not file_path.exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")

        content = file_path.read_text(encoding="utf-8")

        # Check for new extension format
        if str(file_path).endswith((".light.yaml", ".light.yml", ".readable.yaml", ".readable.yml")):
            return yaml.safe_load(content)
        elif str(file_path).endswith(".native.json"):
            return json.loads(content)
        # Fallback to old extension format
        elif file_path.suffix.lower() in [".yaml", ".yml"]:
            return yaml.safe_load(content)
        elif file_path.suffix.lower() == ".json":
            return json.loads(content)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    async def write_file(self, path: str, data: dict[str, Any]) -> None:
        """Write data to a diagram file."""
        file_path = self.diagrams_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Check for new extension format
        if str(file_path).endswith((".light.yaml", ".light.yml", ".readable.yaml", ".readable.yml")):
            content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        elif str(file_path).endswith(".native.json"):
            content = json.dumps(data, indent=2)
        # Fallback to old extension format
        elif file_path.suffix.lower() in [".yaml", ".yml"]:
            content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        elif file_path.suffix.lower() == ".json":
            content = json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        file_path.write_text(content, encoding="utf-8")

    async def delete_file(self, path: str) -> None:
        """Delete a diagram file."""
        file_path = self.diagrams_dir / path
        if not file_path.exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")
        file_path.unlink()

    async def exists(self, path: str) -> bool:
        """Check if a diagram file exists."""
        file_path = self.diagrams_dir / path
        return file_path.exists()

    async def list_files(self) -> list[dict[str, Any]]:
        """List all diagram files with metadata."""
        files = []
        # Support both old and new extensions
        allowed_extensions = [".yaml", ".yml", ".json"]
        new_extensions = [".native.json", ".light.yaml", ".light.yml", ".readable.yaml", ".readable.yml"]

        for file_path in self.diagrams_dir.rglob("*"):
            if file_path.is_file():
                # Check for new extension format first
                matches_new = any(str(file_path).endswith(ext) for ext in new_extensions)
                # Fallback to old extension format
                matches_old = file_path.suffix.lower() in allowed_extensions
                
                if matches_new or matches_old:
                    try:
                        stats = file_path.stat()
                        relative_path = file_path.relative_to(self.diagrams_dir)

                        # Determine the actual extension
                        actual_extension = file_path.suffix
                        for ext in new_extensions:
                            if str(file_path).endswith(ext):
                                actual_extension = ext
                                break

                        file_info = self.domain_service.generate_file_info(
                            path=str(relative_path),
                            name=file_path.stem if not matches_new else str(file_path.name).replace(actual_extension, ""),
                            extension=actual_extension,
                            size=stats.st_size,
                            modified_timestamp=stats.st_mtime,
                        )

                        files.append(file_info)
                    except Exception as e:
                        logger.warning(f"Failed to process file {file_path}: {e}")
                        continue

        files.sort(key=lambda x: x["modified"], reverse=True)
        return files