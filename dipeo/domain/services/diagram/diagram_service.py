# Refactored diagram domain service - contains only business logic, no I/O.

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from dipeo.models import HandleLabel
from dipeo.core import ValidationError

logger = logging.getLogger(__name__)


class DiagramDomainService:
    """Domain service for diagram business logic and validation.
    
    This service contains only business logic - no I/O operations.
    All data is passed in as parameters.
    """

    def validate_diagram_data(self, data: dict[str, Any]) -> None:
        """Validate diagram data structure.
        
        Raises:
            ValidationError: If the diagram data is invalid
        """
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
            # We'll skip detailed validation here since the conversion process handles it
            for conn in connections:
                if not isinstance(conn, dict):
                    raise ValidationError("Each connection must be a dictionary")
                if "from" not in conn or "to" not in conn:
                    raise ValidationError("Each connection must have 'from' and 'to' fields")
        else:
            arrows = data["arrows"]
            if not isinstance(arrows, list):
                raise ValidationError("Arrows must be a list")
                
            # Arrows connect handles, not nodes directly
            # Handle IDs have format: {node_id}_{handle_label} or {node_id}_{handle_label}
            node_ids = {node["id"] for node in data["nodes"]}
            for arrow in arrows:
                if not isinstance(arrow, dict):
                    raise ValidationError("Each arrow must be a dictionary")
                if "source" not in arrow or "target" not in arrow:
                    raise ValidationError("Each arrow must have 'source' and 'target' fields")
                
                # Extract node ID from handle ID
                # Handle format: {nodeId}_{handleLabel} where nodeId contains underscore (e.g., node_ABC)
                # So we need to find the last underscore that separates nodeId from handle label
                source_handle = arrow["source"]
                target_handle = arrow["target"]
                
                # Find the last occurrence of underscore followed by a handle label pattern
                # Common handle labels: default_input, default_output, first_input, etc.
                # Split on the last underscore that precedes these patterns
                source_parts = source_handle.rsplit("_", 2)  # Split from right, max 2 splits
                target_parts = target_handle.rsplit("_", 2)  # Split from right, max 2 splits
                
                # If we have at least 3 parts, the node ID is everything except the last 2 parts
                # e.g., "node_ABC_default_output" -> ["node", "ABC", "default", "output"]
                # rsplit with 2 gives ["node_ABC", "default", "output"]
                if len(source_parts) >= 3 and source_parts[-2] in [x for x in HandleLabel]:
                    source_node_id = source_parts[0]
                elif len(source_parts) >= 2:
                    # Fallback: assume everything before last underscore is node ID
                    source_node_id = "_".join(source_parts[:-1])
                else:
                    source_node_id = arrow["source"]
                    
                if len(target_parts) >= 3 and target_parts[-2] in [x for x in HandleLabel]:
                    target_node_id = target_parts[0]
                elif len(target_parts) >= 2:
                    # Fallback: assume everything before last underscore is node ID
                    target_node_id = "_".join(target_parts[:-1])
                else:
                    target_node_id = arrow["target"]
                
                if source_node_id not in node_ids:
                    raise ValidationError(f"Arrow source node '{source_node_id}' not found in nodes")
                if target_node_id not in node_ids:
                    raise ValidationError(f"Arrow target node '{target_node_id}' not found in nodes")

    def clean_enum_values(self, data: Any) -> Any:
        """Recursively convert enum values to strings in the data structure.
        
        This is pure transformation logic with no I/O.
        """
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

    def determine_format_type(self, path: str) -> str:
        """Determine the format type from the path structure.
        
        This is pure logic based on path analysis.
        """
        path_obj = Path(path)
        parts = path_obj.parts
        
        if len(parts) > 0:
            # Check if path contains format directory
            for part in parts:
                if part in ["native", "light", "readable"]:
                    return part
                    
        # Default to native for files without format directory
        return "native"

    def generate_file_info(
        self,
        path: str,
        name: str,
        extension: str,
        size: int,
        modified_timestamp: float,
    ) -> dict[str, Any]:
        """Generate file info dictionary from provided data.
        
        Pure transformation - no I/O operations.
        """
        path_obj = Path(path)
        format_type = self.determine_format_type(path)
        
        # Generate ID from path (without extension)
        file_id = str(path_obj.with_suffix(""))
        
        return {
            "id": file_id,
            "name": name,
            "path": path,
            "format": format_type,
            "extension": extension.lstrip("."),
            "modified": datetime.fromtimestamp(modified_timestamp, tz=UTC).isoformat(),
            "size": size,
        }

    def validate_file_extension(self, path: str, allowed_extensions: list[str]) -> None:
        """Validate that file has allowed extension.
        
        Raises:
            ValidationError: If extension is not allowed
        """
        path_obj = Path(path)
        extension = path_obj.suffix.lower()
        
        if extension not in [ext.lower() for ext in allowed_extensions]:
            raise ValidationError(
                f"File extension '{extension}' not allowed. "
                f"Allowed extensions: {allowed_extensions}"
            )

    def construct_search_paths(self, diagram_id: str, base_extensions: list[str]) -> list[str]:
        """Construct possible file paths for a diagram ID.
        
        Returns list of relative paths to check.
        """
        paths = []
        
        # Direct paths with extensions
        for ext in base_extensions:
            paths.append(f"{diagram_id}{ext}")
        
        # Only check subdirectories if diagram_id doesn't contain a path separator
        if "/" not in diagram_id:
            subdirs = ["light", "readable", "native"]
            for subdir in subdirs:
                for ext in base_extensions:
                    paths.append(f"{subdir}/{diagram_id}{ext}")
                    
        return paths

    def transform_diagram_for_export(
        self,
        diagram: dict[str, Any],
        target_format: str = "native"
    ) -> dict[str, Any]:
        """Transform diagram data for export to specific format.
        
        Pure transformation logic based on target format.
        """
        # Clean enum values first
        cleaned = self.clean_enum_values(diagram)
        
        if target_format == "light":
            # Remove verbose fields for light format
            if "metadata" in cleaned:
                cleaned["metadata"] = {
                    k: v for k, v in cleaned["metadata"].items()
                    if k in ["name", "version", "description"]
                }
        elif target_format == "readable":
            # Add human-readable annotations
            if "nodes" in cleaned:
                for node in cleaned["nodes"]:
                    if "type" in node:
                        node["_readable_type"] = f"Node Type: {node['type']}"
                        
        return cleaned