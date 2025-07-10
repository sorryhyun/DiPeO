# Infrastructure implementation for diagram file I/O operations.

import json
import logging
from pathlib import Path
from typing import Any

import yaml
from dipeo.core.constants import BASE_DIR
from dipeo.utils.diagram import DiagramBusinessLogic as DiagramDomainService

logger = logging.getLogger(__name__)

from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    runtime_checkable,
)


@runtime_checkable
class SupportsDiagram(Protocol):
    """Protocol for diagram operations."""

    def convert_from_yaml(self, yaml_text: str) -> dict: ...
    def convert_to_llm_yaml(self, diagram: dict) -> str: ...
    def list_diagram_files(
        self, directory: Optional[str] = None
    ) -> List[Dict[str, Any]]: ...
    def load_diagram(self, path: str) -> Dict[str, Any]: ...
    def save_diagram(self, path: str, diagram: Dict[str, Any]) -> None: ...
    def create_diagram(
        self, name: str, diagram: Dict[str, Any], format: str = "json"
    ) -> str: ...
    def update_diagram(self, path: str, diagram: Dict[str, Any]) -> None: ...
    def delete_diagram(self, path: str) -> None: ...
    async def save_diagram_with_id(
        self, diagram_dict: Dict[str, Any], filename: str
    ) -> str: ...
    async def get_diagram(self, diagram_id: str) -> Optional[Dict[str, Any]]: ...


class DiagramFileRepository(BaseService, SupportsDiagram):
    """Infrastructure service for diagram file I/O operations.
    
    This service handles all file system interactions for diagrams.
    Business logic is delegated to DiagramDomainService.
    """

    def __init__(
        self,
        domain_service: DiagramDomainService,
        base_dir: Path | None = None
    ):
        super().__init__()
        self.domain_service = domain_service
        self.diagrams_dir = (base_dir or BASE_DIR) / "files" / "diagrams"

    async def initialize(self) -> None:
        """Ensure diagram directory exists."""
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)

    async def read_file(self, path: str) -> dict[str, Any]:
        """Read diagram file from filesystem.
        
        I/O operation that reads file and parses content.
        """
        file_path = self.diagrams_dir / path

        if not file_path.exists():
            logger.error(
                f"File does not exist: {file_path} (resolved from path: {path})"
            )
            raise FileNotFoundError(f"Diagram file not found: {path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Validate extension using domain service
        allowed_extensions = [".yaml", ".yml", ".json"]
        self.domain_service.validate_file_extension(str(file_path), allowed_extensions)

        try:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                with file_path.open(encoding="utf-8") as f:
                    try:
                        # First try safe_load
                        data = yaml.safe_load(f)
                    except yaml.constructor.ConstructorError as e:
                        # If that fails due to Python objects, try unsafe load
                        logger.warning(f"YAML file {path} contains Python objects: {e}")
                        f.seek(0)
                        data = yaml.unsafe_load(f)
                        # Use domain service to clean enums
                        data = self.domain_service.clean_enum_values(data)
            elif file_path.suffix.lower() == ".json":
                with file_path.open(encoding="utf-8") as f:
                    data = json.load(f)
            
            # Validate diagram structure using domain service
            self.domain_service.validate_diagram_data(data)
            return data

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
        """Write diagram to filesystem.
        
        I/O operation that validates and writes content.
        """
        file_path = self.diagrams_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Validate extension using domain service
        allowed_extensions = [".yaml", ".yml", ".json"]
        self.domain_service.validate_file_extension(str(file_path), allowed_extensions)

        # Validate diagram structure before writing
        self.domain_service.validate_diagram_data(content)
        
        # Determine format and transform if needed
        format_type = self.domain_service.determine_format_type(path)
        transformed_content = self.domain_service.transform_diagram_for_export(
            content, format_type
        )

        try:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                with file_path.open("w", encoding="utf-8") as f:
                    yaml.dump(
                        transformed_content,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    )
            elif file_path.suffix.lower() == ".json":
                with file_path.open("w", encoding="utf-8") as f:
                    json.dump(transformed_content, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            raise

    async def delete_file(self, path: str) -> None:
        """Delete diagram file from filesystem.
        
        Pure I/O operation.
        """
        file_path = self.diagrams_dir / path

        if not file_path.exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")

        try:
            file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            raise

    async def list_files(self, directory: str | None = None) -> list[dict[str, Any]]:
        """List diagram files in directory.
        
        I/O operation that reads filesystem and uses domain service for data transformation.
        """
        files = []

        if directory:
            scan_dir = self.diagrams_dir / directory
        else:
            scan_dir = self.diagrams_dir

        if not scan_dir.exists():
            return files

        allowed_extensions = [".yaml", ".yml", ".json"]
        
        for file_path in scan_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in allowed_extensions:
                try:
                    stats = file_path.stat()
                    relative_path = file_path.relative_to(self.diagrams_dir)
                    
                    # Use domain service to generate file info
                    file_info = self.domain_service.generate_file_info(
                        path=str(relative_path),
                        name=file_path.stem,
                        extension=file_path.suffix,
                        size=stats.st_size,
                        modified_timestamp=stats.st_mtime,
                    )
                    
                    files.append(file_info)

                except Exception:
                    # Skip files that can't be processed
                    continue

        # Sort by modified date (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files

    async def exists(self, path: str) -> bool:
        """Check if diagram file exists.
        
        Pure I/O operation.
        """
        file_path = self.diagrams_dir / path
        return file_path.exists() and file_path.is_file()

    async def find_by_id(self, diagram_id: str) -> str | None:
        """Find diagram file by ID.
        
        Uses domain service to generate search paths, then performs I/O.
        """
        # Get search paths from domain service
        search_paths = self.domain_service.construct_search_paths(
            diagram_id,
            base_extensions=[".yaml", ".yml", ".json"]
        )
        
        # Check each path
        for path in search_paths:
            if await self.exists(path):
                return path
                
        # If not found in standard locations, scan all files
        all_files = await self.list_files()
        for file_info in all_files:
            if file_info["id"] == diagram_id:
                return file_info["path"]

        return None