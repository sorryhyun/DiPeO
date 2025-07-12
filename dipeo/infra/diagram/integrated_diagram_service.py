"""Integrated infrastructure service for diagram operations."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dipeo.core.constants import BASE_DIR
from dipeo.core.ports.diagram_port import DiagramPort
from dipeo.diagram.unified_converter import UnifiedDiagramConverter
from dipeo.domain.diagram.services import DiagramBusinessLogic as DiagramDomainService
from typing import Any, Dict, Optional, Union

from dipeo.core.ports import FileServicePort
from dipeo.diagram import BackendDiagram, backend_to_graphql
from dipeo.diagram.unified_converter import UnifiedDiagramConverter
from dipeo.models import DiagramFormat, DomainDiagram


logger = logging.getLogger(__name__)


class IntegratedDiagramService(DiagramPort):
    def __init__(self, file_service: FileServicePort):
        self.file_service = file_service
        self.converter = UnifiedDiagramConverter()
        self.diagrams_dir = Path(BASE_DIR) / "files" / "diagrams"
        self.domain_service = DiagramDomainService()

    def detect_format(self, content: str) -> DiagramFormat:
        content = content.strip()

        if content.startswith('{'):
            import json
            try:
                data = json.loads(content)
                if "nodes" in data and isinstance(data["nodes"], dict):
                    return DiagramFormat.native
                return DiagramFormat.native
            except json.JSONDecodeError:
                pass

        try:
            import yaml
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                if (data.get("version") == "light" or
                        (isinstance(data.get("nodes"), list) and
                         "connections" in data and
                         "persons" in data)):
                    return DiagramFormat.light
                if data.get("format") == "readable":
                    return DiagramFormat.readable
                return DiagramFormat.light
        except yaml.YAMLError:
            pass

        raise ValueError("Unable to detect diagram format")

    def load_diagram(
            self,
            content: str,
            format: Optional[DiagramFormat] = None,
    ) -> DomainDiagram:
        if format is None:
            format = self.detect_format(content)

        return self.converter.deserialize(content, format_id=format.value)

    async def load_from_file(
            self,
            file_path: str,
            format: Optional[DiagramFormat] = None,
    ) -> DomainDiagram:
        result = self.file_service.read(file_path)
        content = result.get("content", "")

        if not content:
            raise ValueError(f"Empty or missing content in file: {file_path}")

        return self.load_diagram(content, format)


    
    def list_diagrams(self, directory: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.list_diagram_files(directory)
    
    def list_diagram_files(self, directory: Optional[str] = None) -> List[Dict[str, Any]]:
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
    

    def save_diagram(self, path: str, diagram: Dict[str, Any]) -> None:
        file_path = self.diagrams_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.domain_service.validate_diagram_data(diagram)
        
        format_type = self.domain_service.determine_format_type(path)
        
        if file_path.suffix.lower() in [".yaml", ".yml"]:
            content = self.converter.dict_to_yaml(diagram, format_type=format_type)
            file_path.write_text(content, encoding="utf-8")
        elif file_path.suffix.lower() == ".json":
            content = self.converter.dict_to_json(diagram, format_type=format_type)
            file_path.write_text(content, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def create_diagram(self, name: str, diagram: Dict[str, Any], format: str = "json") -> str:
        format_type = "native" if format == "json" else format
        format_dir = self.diagrams_dir / format_type
        format_dir.mkdir(parents=True, exist_ok=True)
        
        extension = ".json" if format == "json" else ".yaml"
        filename = f"{name}{extension}"
        path = f"{format_type}/{filename}"
        
        self.save_diagram(path, diagram)
        return path
    
    def update_diagram(self, path: str, diagram: Dict[str, Any]) -> None:
        if not (self.diagrams_dir / path).exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")
        
        self.save_diagram(path, diagram)
    
    def delete_diagram(self, path: str) -> None:
        file_path = self.diagrams_dir / path
        
        if not file_path.exists():
            raise FileNotFoundError(f"Diagram file not found: {path}")
        
        file_path.unlink()
    
    async def save_diagram_with_id(self, diagram_dict: Dict[str, Any], filename: str) -> str:
        if filename.endswith(".json"):
            format_type = "native"
        elif filename.endswith((".yaml", ".yml")):
            if "light" in filename:
                format_type = "light"
            elif "readable" in filename:
                format_type = "readable"
            else:
                format_type = "native"
        else:
            format_type = "native"
        
        path = f"{format_type}/{filename}"
        self.save_diagram(path, diagram_dict)
        
        return diagram_dict.get("id", filename)
    
    async def get_diagram(self, diagram_id: str) -> Optional[Dict[str, Any]]:
        search_paths = self.domain_service.construct_search_paths(
            diagram_id,
            base_extensions=[".yaml", ".yml", ".json"]
        )
        
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