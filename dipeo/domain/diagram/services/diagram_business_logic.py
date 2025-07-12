"""Diagram business logic - pure functions for diagram operations."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from dipeo.core import ValidationError
from dipeo.domain.file.value_objects import FileExtension, FileSize
from dipeo.models import DiagramFormat, HandleLabel

logger = logging.getLogger(__name__)


class DiagramBusinessLogic:
    """Pure business logic for diagram operations and validation."""

    def validate_diagram_data(self, data: dict[str, Any]) -> None:
        """Validate diagram data structure."""
        if not isinstance(data, dict):
            raise ValidationError("Diagram data must be a dictionary")
            
        # Detect format and validate accordingly
        is_light_format = (
            data.get("version") == "light" or
            (isinstance(data.get("nodes"), list) and 
             "connections" in data and 
             "persons" in data)
        )
        
        # Check required fields based on format
        if is_light_format:
            required_fields = ["nodes", "connections"]
        else:
            required_fields = ["nodes", "arrows"]
            
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Diagram must contain '{field}' field")
                
        # Validate nodes
        nodes = data["nodes"]
        if is_light_format:
            if not isinstance(nodes, list):
                raise ValidationError("Nodes must be a list in light format")
            # Light format nodes don't require 'id' field (it's generated)
        else:
            if not isinstance(nodes, list):
                raise ValidationError("Nodes must be a list")
            for node in nodes:
                if not isinstance(node, dict):
                    raise ValidationError("Each node must be a dictionary")
                if "id" not in node:
                    raise ValidationError("Each node must have an 'id' field")
                
        # Validate arrows/connections
        if is_light_format:
            connections = data["connections"]
            if not isinstance(connections, list):
                raise ValidationError("Connections must be a list")
            
            # For light format, connections use labels instead of IDs
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
        """Validate arrow connections."""
        node_ids = {node["id"] for node in nodes}
        
        for arrow in arrows:
            if not isinstance(arrow, dict):
                raise ValidationError("Each arrow must be a dictionary")
            if "source" not in arrow or "target" not in arrow:
                raise ValidationError("Each arrow must have 'source' and 'target' fields")
            
            # Extract node IDs from handle IDs
            source_node_id = self._extract_node_id_from_handle(arrow["source"])
            target_node_id = self._extract_node_id_from_handle(arrow["target"])
            
            if source_node_id not in node_ids:
                raise ValidationError(f"Arrow source node '{source_node_id}' not found in nodes")
            if target_node_id not in node_ids:
                raise ValidationError(f"Arrow target node '{target_node_id}' not found in nodes")

    def _extract_node_id_from_handle(self, handle_id: str) -> str:
        """Extract node ID from handle ID."""
        # Handle format: {nodeId}_{handleLabel} where nodeId may contain underscore
        parts = handle_id.rsplit("_", 2)  # Split from right, max 2 splits
        
        # Check if the second-to-last part is a valid handle label
        if len(parts) >= 3 and parts[-2] in [label.value for label in HandleLabel]:
            return parts[0]
        elif len(parts) >= 2:
            # Fallback: assume everything before last underscore is node ID
            return "_".join(parts[:-1])
        else:
            return handle_id

    def clean_enum_values(self, data: Any) -> Any:
        """Recursively convert enum values to strings in the data structure."""
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
        """Determine the format type from the path structure."""
        path_obj = Path(path)
        parts = path_obj.parts
        
        # Check if path contains format directory
        for part in parts:
            try:
                return DiagramFormat(part)
            except ValueError:
                continue
                
        # Default to native for files without format directory
        return DiagramFormat.native

    def generate_file_info(
        self,
        path: str,
        name: str,
        extension: str,
        size: int,
        modified_timestamp: float,
    ) -> dict[str, Any]:
        """Generate file info dictionary from provided data."""
        path_obj = Path(path)
        format_type = self.determine_format_type(path)
        file_size = FileSize(size)
        file_extension = FileExtension(extension) if extension else None
        
        # Generate ID from path (without extension)
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
        """Validate that file has allowed extension."""
        path_obj = Path(path)
        
        if not path_obj.suffix:
            raise ValidationError("File must have an extension")
            
        extension = FileExtension(path_obj.suffix)
        
        # Normalize allowed extensions
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
        """Construct possible file paths for a diagram ID."""
        paths = []
        
        # Normalize extensions
        extensions = [
            FileExtension(ext if ext.startswith('.') else f'.{ext}').value
            for ext in base_extensions
        ]
        
        # Direct paths with extensions
        for ext in extensions:
            paths.append(f"{diagram_id}{ext}")
        
        # Only check subdirectories if diagram_id doesn't contain a path separator
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
        """Transform diagram data for export to specific format."""
        # Clean enum values first
        cleaned = self.clean_enum_values(diagram)
        
        if target_format == DiagramFormat.light:
            # Remove verbose fields for light format
            if "metadata" in cleaned:
                cleaned["metadata"] = {
                    k: v for k, v in cleaned["metadata"].items()
                    if k in ["name", "version", "description"]
                }
        elif target_format == DiagramFormat.readable:
            # Add human-readable annotations
            if "nodes" in cleaned:
                for node in cleaned["nodes"]:
                    if "type" in node:
                        node["_readable_type"] = f"Node Type: {node['type']}"
                        
        return cleaned

    def is_valid_diagram_format(self, format_string: str) -> bool:
        """Check if a string is a valid diagram format."""
        try:
            DiagramFormat(format_string)
            return True
        except ValueError:
            return False

    def get_diagram_file_extensions(self) -> list[str]:
        """Get standard file extensions for diagram files."""
        return [".json", ".yaml", ".yml"]