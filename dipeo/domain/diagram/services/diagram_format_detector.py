"""Unified service for diagram format detection, validation, and transformation."""

import json
from pathlib import Path
from typing import Any

import yaml

from dipeo.core import ValidationError
from dipeo.models import DiagramFormat, HandleLabel


class DiagramFormatDetector:
    """Handles all diagram format-related operations including detection, validation, and transformation."""

    def detect_format(self, content: str) -> DiagramFormat:
        """Detect diagram format from content."""
        content = content.strip()

        if content.startswith('{'):
            try:
                data = json.loads(content)
                if "nodes" in data and isinstance(data["nodes"], dict):
                    return DiagramFormat.NATIVE
                return DiagramFormat.NATIVE
            except json.JSONDecodeError:
                pass

        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                if (data.get("version") == "light" or
                        (isinstance(data.get("nodes"), list) and
                         "connections" in data and
                         "persons" in data)):
                    return DiagramFormat.LIGHT
                if data.get("format") == "readable":
                    return DiagramFormat.READABLE
                return DiagramFormat.LIGHT
        except yaml.YAMLError:
            pass

        raise ValueError("Unable to detect diagram format")

    def detect_format_from_filename(self, filename: str) -> DiagramFormat | None:
        """Determine format from filename patterns."""
        if filename.endswith(".native.json"):
            return DiagramFormat.NATIVE
        elif filename.endswith(".light.yaml") or filename.endswith(".light.yml"):
            return DiagramFormat.LIGHT
        elif filename.endswith(".readable.yaml") or filename.endswith(".readable.yml"):
            return DiagramFormat.READABLE
        elif filename.endswith(".json"):
            return DiagramFormat.NATIVE
        elif filename.endswith((".yaml", ".yml")):
            if "light" in filename.lower():
                return DiagramFormat.LIGHT
            elif "readable" in filename.lower():
                return DiagramFormat.READABLE
            return DiagramFormat.LIGHT
        return None

    def validate_format(self, content: str, format: DiagramFormat) -> bool:
        """Validate content matches expected format."""
        try:
            detected_format = self.detect_format(content)
            if detected_format != format:
                raise ValueError(
                    f"Content format mismatch. Expected {format.value}, "
                    f"but detected {detected_format.value}"
                )
            return True
        except Exception as e:
            raise ValueError(f"Invalid {format.value} format: {e!s}")

    def validate_diagram_structure(self, data: dict[str, Any], format: DiagramFormat | None = None) -> None:
        """Validate diagram data structure based on format."""
        if not isinstance(data, dict):
            raise ValidationError("Diagram data must be a dictionary")
        
        # Auto-detect format if not provided
        if format is None:
            is_light_format = (
                data.get("version") == "light" or
                (isinstance(data.get("nodes"), list) and 
                 "connections" in data and 
                 "persons" in data)
            )
            format = DiagramFormat.LIGHT if is_light_format else DiagramFormat.NATIVE
        
        if format == DiagramFormat.NATIVE:
            self._validate_native_structure(data)
        elif format == DiagramFormat.LIGHT:
            self._validate_light_structure(data)
        elif format == DiagramFormat.READABLE:
            self._validate_readable_structure(data)

    def _validate_native_structure(self, data: dict[str, Any]) -> None:
        """Validate native format structure."""
        if "nodes" not in data:
            raise ValidationError("Native format requires 'nodes' field")
        if "arrows" not in data:
            raise ValidationError("Native format requires 'arrows' field")
        
        nodes = data["nodes"]
        if not isinstance(nodes, (dict, list)):
            raise ValidationError("Nodes must be a dictionary or list in native format")
        
        # Validate arrows reference valid nodes
        if isinstance(nodes, list):
            node_ids = {node["id"] for node in nodes if isinstance(node, dict) and "id" in node}
        else:
            node_ids = set(nodes.keys())
        
        arrows = data["arrows"]
        if not isinstance(arrows, (dict, list)):
            raise ValidationError("Arrows must be a dictionary or list")
        
        arrow_list = list(arrows.values()) if isinstance(arrows, dict) else arrows
        for arrow in arrow_list:
            if not isinstance(arrow, dict):
                raise ValidationError("Each arrow must be a dictionary")
            if "source" not in arrow or "target" not in arrow:
                raise ValidationError("Each arrow must have 'source' and 'target' fields")

    def _validate_light_structure(self, data: dict[str, Any]) -> None:
        """Validate light format structure."""
        required_fields = ["nodes", "connections", "persons"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Light format requires '{field}' field")
        
        if not isinstance(data["nodes"], list):
            raise ValidationError("Light format requires 'nodes' to be a list")
        
        for node in data["nodes"]:
            if not isinstance(node, dict):
                raise ValidationError("Each node must be a dictionary")
            if "id" not in node:
                raise ValidationError("Each node must have an 'id' field")
        
        connections = data["connections"]
        if not isinstance(connections, list):
            raise ValidationError("Connections must be a list")
        
        for conn in connections:
            if not isinstance(conn, dict):
                raise ValidationError("Each connection must be a dictionary")
            if "from" not in conn or "to" not in conn:
                raise ValidationError("Each connection must have 'from' and 'to' fields")

    def _validate_readable_structure(self, data: dict[str, Any]) -> None:
        """Validate readable format structure."""
        if data.get("format") != "readable" and "readable" not in str(data):
            raise ValidationError("Readable format should indicate its format type")

    def get_file_extension(self, format: DiagramFormat) -> str:
        """Get appropriate file extension for format."""
        if format == DiagramFormat.NATIVE:
            return ".native.json"
        elif format == DiagramFormat.LIGHT:
            return ".light.yaml"
        elif format == DiagramFormat.READABLE:
            return ".readable.yaml"
        else:
            return ".light.yaml"

    def construct_search_patterns(
        self, diagram_id: str, formats: list[DiagramFormat] | None = None
    ) -> list[str]:
        """Construct file search patterns for diagram loading."""
        if formats is None:
            formats = [DiagramFormat.NATIVE, DiagramFormat.LIGHT, DiagramFormat.READABLE]
        
        patterns = []
        
        # Check if already has valid extension
        has_valid_extension = any(
            diagram_id.endswith(ext) for ext in 
            [".light.yaml", ".native.json", ".readable.yaml"]
        )
        
        if has_valid_extension:
            patterns.append(diagram_id)
            return patterns
        
        # Add patterns with format-specific extensions
        for format in formats:
            ext = self.get_file_extension(format)
            patterns.append(f"{diagram_id}{ext}")
            patterns.append(f"{format.value}/{diagram_id}{ext}")
        
        # Legacy patterns for backward compatibility
        old_extensions = [".yaml", ".yml", ".json"]
        for format in formats:
            format_dir = format.value
            for ext in old_extensions:
                patterns.append(f"{format_dir}/{diagram_id}{ext}")
        
        for ext in old_extensions:
            patterns.append(f"{diagram_id}{ext}")
        
        return patterns

    def transform_for_export(
        self,
        diagram: dict[str, Any],
        target_format: DiagramFormat
    ) -> dict[str, Any]:
        """Transform diagram data for export to specific format."""
        cleaned = self._clean_enum_values(diagram)
        
        if target_format == DiagramFormat.LIGHT:
            # Simplify metadata for light format
            if "metadata" in cleaned:
                cleaned["metadata"] = {
                    k: v for k, v in cleaned["metadata"].items()
                    if k in ["name", "version", "description"]
                }
        elif target_format == DiagramFormat.READABLE:
            # Add readable annotations
            if "nodes" in cleaned:
                for node in cleaned["nodes"]:
                    if "type" in node:
                        node["_readable_type"] = f"Node Type: {node['type']}"
        
        return cleaned

    def _clean_enum_values(self, data: Any) -> Any:
        """Recursively clean enum values to their string representation."""
        if isinstance(data, dict):
            return {
                key: value.value if hasattr(value, 'value') else self._clean_enum_values(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                item.value if hasattr(item, 'value') else self._clean_enum_values(item)
                for item in data
            ]
        return data

    def extract_node_id_from_handle(self, handle_id: str) -> str:
        """Extract node ID from a handle identifier."""
        parts = handle_id.rsplit("_", 2)  # Split from right, max 2 splits
        
        if len(parts) >= 3 and parts[-2] in [label.value for label in HandleLabel]:
            return parts[0]
        elif len(parts) >= 2:
            return "_".join(parts[:-1])
        else:
            return handle_id