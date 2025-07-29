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
        self.diagrams_dir = self.base_dir / "files"

    async def initialize(self) -> None:
        # Initialize the repository by ensuring directories exist
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)

    async def find_by_id(self, diagram_id: str) -> str | None:
        """Find a diagram file by ID."""
        # Construct possible paths for the diagram with new extensions
        search_paths = self.domain_service.construct_search_paths(
            diagram_id, base_extensions=[".native.json", ".light.yaml", ".readable.yaml"]
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

        # Handle only new extension formats
        if str(file_path).endswith((".light.yaml", ".readable.yaml")):
            return yaml.safe_load(content)
        elif str(file_path).endswith(".native.json"):
            return json.loads(content)
        else:
            raise ValueError(f"Unsupported file format: {path}")

    async def read_raw_content(self, path: str) -> str:
        """Read a diagram file and return raw content."""
        file_path = self.diagrams_dir / path
        if not file_path.exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")

        return file_path.read_text(encoding="utf-8")

    async def write_file(self, path: str, data: dict[str, Any] | str) -> None:
        """Write data to a diagram file."""
        file_path = self.diagrams_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle only new extension formats
        if str(file_path).endswith((".light.yaml", ".readable.yaml")):
            if isinstance(data, str):
                # If already a string (e.g., from conversion), write as-is
                content = data
            else:
                content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        elif str(file_path).endswith(".native.json"):
            if isinstance(data, str):
                # If already a string (e.g., from conversion), write as-is
                content = data
            else:
                content = json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported file format: {path}")

        # Write directly without creating backup
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
        # Only support new extension formats
        diagram_extensions = [
            ".native.json",
            ".light.yaml",
            ".readable.yaml",
        ]

        # Load all files in the directory
        for file_path in self.diagrams_dir.rglob("*"):
            if file_path.is_file():
                # Skip manifest files
                if "manifest" in str(file_path).lower():
                    continue
                
                # Skip codegen diagrams - only show diagrams from files/diagrams/
                relative_path_str = str(file_path.relative_to(self.diagrams_dir))
                if relative_path_str.startswith("codegen/"):
                    continue

                # Check if file has a diagram extension
                for ext in diagram_extensions:
                    if str(file_path).endswith(ext):
                        try:
                            stats = file_path.stat()
                            relative_path = file_path.relative_to(self.diagrams_dir)

                            # Extract the base name by removing the extension
                            base_name = str(file_path.name).replace(ext, "")

                            file_info = self.domain_service.generate_file_info(
                                path=str(relative_path),
                                name=base_name,
                                extension=ext,
                                size=stats.st_size,
                                modified_timestamp=stats.st_mtime,
                            )

                            files.append(file_info)
                        except Exception as e:
                            logger.warning(f"Failed to process file {file_path}: {e}")
                            continue
                        break  # Found a matching extension, no need to check others

        # Sort by modified time, most recent first
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files
