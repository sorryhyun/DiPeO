"""Integrated infrastructure service for diagram operations."""

import logging
from pathlib import Path
from typing import Any

from dipeo.core.constants import BASE_DIR
from dipeo.core.ports import FileServicePort
from dipeo.core.ports.diagram_port import DiagramPort
from dipeo.diagram.unified_converter import UnifiedDiagramConverter
from dipeo.domain.diagram.services import DiagramBusinessLogic as DiagramDomainService
from dipeo.domain.diagram.services import DiagramFormatService
from dipeo.models import DiagramFormat, DomainDiagram

logger = logging.getLogger(__name__)


class IntegratedDiagramService(DiagramPort):
    def __init__(self, file_service: FileServicePort):
        self.file_service = file_service
        self.converter = UnifiedDiagramConverter()
        self.diagrams_dir = Path(BASE_DIR) / "files" / "diagrams"
        self.domain_service = DiagramDomainService()
        self.format_service = DiagramFormatService()

    def detect_format(self, content: str) -> DiagramFormat:
        """Delegate format detection to domain service."""
        return self.format_service.detect_format(content)

    def load_diagram(
            self,
            content: str,
            format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        if format is None:
            format = self.format_service.detect_format(content)

        return self.converter.deserialize(content, format_id=format.value)

    async def load_from_file(
            self,
            file_path: str,
            format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        result = self.file_service.read(file_path)
        content = result.get("content", "")

        if not content:
            raise ValueError(f"Empty or missing content in file: {file_path}")

        return self.load_diagram(content, format)


    
    def list_diagrams(self, directory: str | None = None) -> list[dict[str, Any]]:
        return self.list_diagram_files(directory)
    
    def list_diagram_files(self, directory: str | None = None) -> list[dict[str, Any]]:
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
                    
                    file_info = self.domain_service.generate_file_info(
                        path=str(relative_path),
                        name=file_path.stem,
                        extension=file_path.suffix,
                        size=stats.st_size,
                        modified_timestamp=stats.st_mtime,
                    )
                    
                    files.append(file_info)
                except Exception:
                    continue
        
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files
    

    def save_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        file_path = self.diagrams_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.domain_service.validate_diagram_data(diagram)
        
        # Determine format from path
        format = self.format_service.determine_format_from_filename(path)
        if format is None:
            # Fallback to native format
            format = DiagramFormat.native
        format_type = format.value
        
        if file_path.suffix.lower() in [".yaml", ".yml"]:
            content = self.converter.dict_to_yaml(diagram, format_type=format_type)
            file_path.write_text(content, encoding="utf-8")
        elif file_path.suffix.lower() == ".json":
            content = self.converter.dict_to_json(diagram, format_type=format_type)
            file_path.write_text(content, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def create_diagram(self, name: str, diagram: dict[str, Any], format: str = "json") -> str:
        # Determine format based on requested format
        if format == "json":
            diagram_format = DiagramFormat.native
        else:
            diagram_format = DiagramFormat.light  # Default to light for YAML
        
        format_type = diagram_format.value
        format_dir = self.diagrams_dir / format_type
        format_dir.mkdir(parents=True, exist_ok=True)
        
        extension = self.format_service.get_file_extension_for_format(diagram_format)
        filename = f"{name}{extension}"
        path = f"{format_type}/{filename}"
        
        self.save_diagram(path, diagram)
        return path
    
    def update_diagram(self, path: str, diagram: dict[str, Any]) -> None:
        if not (self.diagrams_dir / path).exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")
        
        self.save_diagram(path, diagram)
    
    def delete_diagram(self, path: str) -> None:
        file_path = self.diagrams_dir / path
        
        if not file_path.exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")
        
        file_path.unlink()
    
    async def save_diagram_with_id(self, diagram_dict: dict[str, Any], filename: str) -> str:
        # Determine format from filename
        detected_format = self.format_service.determine_format_from_filename(filename)
        if detected_format:
            format_type = detected_format.value
        else:
            format_type = "native"  # Default
        
        path = f"{format_type}/{filename}"
        self.save_diagram(path, diagram_dict)
        
        return diagram_dict.get("id", filename)
    
    async def get_diagram(self, diagram_id: str) -> dict[str, Any] | None:
        # Use format service to construct search patterns
        search_paths = self.format_service.construct_search_patterns(diagram_id)
        
        for path in search_paths:
            file_path = self.diagrams_dir / path
            if file_path.exists():
                return self.load_diagram(path)
        
        all_files = self.list_diagram_files()
        for file_info in all_files:
            try:
                diagram = self.load_diagram(file_info["path"])
                if diagram.get("id") == diagram_id:
                    return diagram
            except Exception:
                continue
        
        return None