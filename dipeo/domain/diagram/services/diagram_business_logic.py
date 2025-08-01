"""Diagram business logic - pure functions for diagram operations."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dipeo.core import ValidationError
from dipeo.domain.file.value_objects import FileExtension, FileSize
from dipeo.models import DiagramFormat, HandleLabel

logger = logging.getLogger(__name__)


class DiagramBusinessLogic:

    def validate_diagram_data(self, data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValidationError("Diagram data must be a dictionary")
            
        is_light_format = (
            data.get("version") == "light" or
            (isinstance(data.get("nodes"), list) and 
             "connections" in data and 
             "persons" in data)
        )
        if is_light_format:
            required_fields = ["nodes", "connections"]
        else:
            required_fields = ["nodes", "arrows"]
            
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Diagram must contain '{field}' field")
        nodes = data["nodes"]
        if is_light_format:
            if not isinstance(nodes, list):
                raise ValidationError("Nodes must be a list in light format")
        else:
            if not isinstance(nodes, list):
                raise ValidationError("Nodes must be a list")
            for node in nodes:
                if not isinstance(node, dict):
                    raise ValidationError("Each node must be a dictionary")
                if "id" not in node:
                    raise ValidationError("Each node must have an 'id' field")
        if is_light_format:
            connections = data["connections"]
            if not isinstance(connections, list):
                raise ValidationError("Connections must be a list")
            for conn in connections:
                if not isinstance(conn, dict):
                    raise ValidationError("Each connection must be a dictionary")
                if "from" not in conn or "to" not in conn:
                    raise ValidationError("Each connection must have 'from' and 'to' fields")
        else:
            arrows = data["arrows"]
            if not isinstance(arrows, list):
                raise ValidationError("Arrows must be a list")
                
            self._validate_arrows(arrows, data["nodes"])

    def _validate_arrows(self, arrows: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> None:
        node_ids = {node["id"] for node in nodes}
        
        for arrow in arrows:
            if not isinstance(arrow, dict):
                raise ValidationError("Each arrow must be a dictionary")
            if "source" not in arrow or "target" not in arrow:
                raise ValidationError("Each arrow must have 'source' and 'target' fields")
            source_node_id = self._extract_node_id_from_handle(arrow["source"])
            target_node_id = self._extract_node_id_from_handle(arrow["target"])
            
            if source_node_id not in node_ids:
                raise ValidationError(f"Arrow source node '{source_node_id}' not found in nodes")
            if target_node_id not in node_ids:
                raise ValidationError(f"Arrow target node '{target_node_id}' not found in nodes")

    def _extract_node_id_from_handle(self, handle_id: str) -> str:
        parts = handle_id.rsplit("_", 2)  # Split from right, max 2 splits
        
        if len(parts) >= 3 and parts[-2] in [label.value for label in HandleLabel]:
            return parts[0]
        elif len(parts) >= 2:
            return "_".join(parts[:-1])
        else:
            return handle_id

    def clean_enum_values(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                key: value.value if hasattr(value, 'value') else self.clean_enum_values(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                item.value if hasattr(item, 'value') else self.clean_enum_values(item)
                for item in data
            ]
        return data

    def determine_format_type(self, path: str) -> DiagramFormat:
        path_obj = Path(path)
        parts = path_obj.parts
        
        for part in parts:
            try:
                return DiagramFormat(part)
            except ValueError:
                continue
        return DiagramFormat.NATIVE

    def generate_file_info(
        self,
        path: str,
        name: str,
        extension: str,
        size: int,
        modified_timestamp: float,
    ) -> dict[str, Any]:
        path_obj = Path(path)
        format_type = self.determine_format_type(path)
        file_size = FileSize(size)
        file_extension = FileExtension(extension) if extension else None
        
        path_str = str(path_obj)
        for ext in [".native.json", ".light.yaml", ".readable.yaml"]:
            if path_str.endswith(ext):
                file_id = path_str[:-len(ext)]
                break
        else:
            file_id = str(path_obj.with_suffix(""))
        
        return {
            "id": file_id,
            "name": name,
            "path": path,
            "format": format_type.value,
            "extension": file_extension.without_dot if file_extension else "",
            "modified": datetime.fromtimestamp(modified_timestamp, tz=UTC).isoformat(),
            "size": file_size.bytes,
            "size_human": file_size.human_readable(),
        }

    def validate_file_extension(self, path: str, allowed_extensions: list[str]) -> None:
        path_obj = Path(path)
        
        if not path_obj.suffix:
            raise ValidationError("File must have an extension")
            
        extension = FileExtension(path_obj.suffix)
        
        normalized_allowed = {
            ext if ext.startswith('.') else f'.{ext}'
            for ext in allowed_extensions
        }
        
        if not extension.is_allowed(normalized_allowed):
            raise ValidationError(
                f"File extension '{extension}' not allowed. "
                f"Allowed extensions: {sorted(normalized_allowed)}"
            )

    def construct_search_paths(self, diagram_id: str, base_extensions: list[str]) -> list[str]:
        paths = []
        
        path_obj = Path(diagram_id)
        has_valid_extension = any(
            diagram_id.endswith(ext) for ext in 
            [".light.yaml", ".native.json", ".readable.yaml"]
        )
        
        if has_valid_extension:
            paths.append(diagram_id)
        
        extensions = [
            FileExtension(ext if ext.startswith('.') else f'.{ext}').value
            for ext in base_extensions
        ]
        
        if not has_valid_extension:
            for ext in extensions:
                paths.append(f"{diagram_id}{ext}")
        
        if "/" not in diagram_id:
            for format_type in DiagramFormat:
                for ext in extensions:
                    paths.append(f"{format_type.value}/{diagram_id}{ext}")
                    
        return paths

    def transform_diagram_for_export(
        self,
        diagram: dict[str, Any],
        target_format: DiagramFormat
    ) -> dict[str, Any]:
        cleaned = self.clean_enum_values(diagram)
        
        if target_format == DiagramFormat.LIGHT:
            if "metadata" in cleaned:
                cleaned["metadata"] = {
                    k: v for k, v in cleaned["metadata"].items()
                    if k in ["name", "version", "description"]
                }
        elif target_format == DiagramFormat.READABLE:
            if "nodes" in cleaned:
                for node in cleaned["nodes"]:
                    if "type" in node:
                        node["_readable_type"] = f"Node Type: {node['type']}"
                        
        return cleaned

    def is_valid_diagram_format(self, format_string: str) -> bool:
        try:
            DiagramFormat(format_string)
            return True
        except ValueError:
            return False

    def get_diagram_file_extensions(self) -> list[str]:
        return [".json", ".yaml", ".yml"]