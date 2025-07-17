"""File repository for diagram persistence."""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from dipeo.core.constants import BASE_DIR
from dipeo.domain.diagram.services import DiagramBusinessLogic as DiagramDomainService
from dipeo.models import DiagramFormat, DomainDiagram

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
        # Find a diagram file by ID
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
        # Read a diagram file
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
        # Write a diagram file
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
        # Delete a diagram file
        file_path = self.diagrams_dir / path
        if not file_path.exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")
        file_path.unlink()

    async def exists(self, path: str) -> bool:
        # Check if a diagram file exists
        file_path = self.diagrams_dir / path
        return file_path.exists()

    async def list_files(self) -> list[dict[str, Any]]:
        # List all diagram files
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
    
    def detect_format(self, content: str) -> DiagramFormat:
        # Detect the format of diagram content
        content = content.strip()
        if content.startswith('{'):
            return DiagramFormat.native
        else:
            return DiagramFormat.light
    
    def load_diagram(
        self,
        content: str,
        format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        # Load a diagram from string content
        if format is None:
            format = self.detect_format(content)
        
        if format == DiagramFormat.native:
            data = json.loads(content)
        elif format == DiagramFormat.light:
            data = yaml.safe_load(content)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return DomainDiagram(**data)
    
    async def load_from_file(
        self,
        file_path: str,
        format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        # Load a diagram from a file path
        # Convert absolute path to relative if needed
        path = Path(file_path)
        if path.is_absolute():
            # Try to make it relative to diagrams_dir
            try:
                relative_path = path.relative_to(self.diagrams_dir)
            except ValueError:
                # Path is not under diagrams_dir, use as is
                relative_path = path
        else:
            relative_path = Path(file_path)
        
        data = await self.read_file(str(relative_path))
        return DomainDiagram(**data)
    
    def list_diagrams(self, directory: str | None = None) -> list[dict[str, Any]]:
        # List all diagrams synchronously
        # This is a sync wrapper around the async list_files method
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.list_files())
    
    def save_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        # Save a diagram synchronously
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.write_file(path, diagram))
    
    def create_diagram(
        self, name: str, diagram: dict[str, Any], format: str = "json"
    ) -> str:
        # Create a new diagram and return its path
        # Determine the format type
        if format == "json":
            diagram_format = DiagramFormat.native
            extension = ".native.json"
        elif format == "yaml":
            # Determine light vs readable from diagram content
            if diagram.get("format") == "readable" or diagram.get("version") == "readable":
                diagram_format = DiagramFormat.readable
                extension = ".readable.yaml"
            else:
                diagram_format = DiagramFormat.light
                extension = ".light.yaml"
        else:
            # Default to light format for unknown formats
            diagram_format = DiagramFormat.light
            extension = ".light.yaml"
        
        filename = f"{name}{extension}"
        
        # Ensure unique filename
        path = filename
        counter = 1
        while (self.diagrams_dir / path).exists():
            path = f"{name}_{counter}{extension}"
            counter += 1
        
        self.save_diagram(path, diagram)
        return path
    
    def update_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        # Update an existing diagram
        self.save_diagram(path, diagram)
    
    def delete_diagram(self, path: str) -> None:
        # Delete a diagram synchronously
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.delete_file(path))
    
    async def save_diagram_with_id(
        self, diagram_dict: dict[str, Any], filename: str
    ) -> str:
        # Save a diagram with an ID and return the path
        # Ensure the diagram has an ID
        if "id" not in diagram_dict:
            diagram_dict["id"] = filename.split(".")[0]
        
        await self.write_file(filename, diagram_dict)
        return filename
    
    async def get_diagram(self, diagram_id: str) -> dict[str, Any] | None:
        # Get a diagram by ID
        path = await self.find_by_id(diagram_id)
        if path is None:
            return None
        
        return await self.read_file(path)