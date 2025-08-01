"""Domain service for diagram format detection and validation."""

import json

import yaml

from dipeo.models import DiagramFormat


class DiagramFormatService:
    """Business logic for diagram format detection and validation."""

    def detect_format(self, content: str) -> DiagramFormat:
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

    def validate_format(self, content: str, format: DiagramFormat) -> bool:
        """Returns True if valid, raises ValueError if invalid."""
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

    def determine_format_from_filename(self, filename: str) -> DiagramFormat | None:
        """Uses filename patterns to determine format."""
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

    def get_file_extension_for_format(self, format: DiagramFormat) -> str:
        if format == DiagramFormat.NATIVE:
            return ".native.json"
        elif format == DiagramFormat.LIGHT:
            return ".light.yaml"
        elif format == DiagramFormat.READABLE:
            return ".readable.yaml"
        else:
            return ".light.yaml"

    def construct_search_patterns(
        self, diagram_id: str, formats: list | None = None
    ) -> list:
        if formats is None:
            formats = [DiagramFormat.NATIVE, DiagramFormat.LIGHT, DiagramFormat.READABLE]
        
        patterns = []
        
        for format in formats:
            ext = self.get_file_extension_for_format(format)
            patterns.append(f"{diagram_id}{ext}")
            patterns.append(f"{format.value}/{diagram_id}{ext}")
        
        old_extensions = [".yaml", ".yml", ".json"]
        for format in formats:
            format_dir = format.value
            for ext in old_extensions:
                patterns.append(f"{format_dir}/{diagram_id}{ext}")
        
        for ext in old_extensions:
            patterns.append(f"{diagram_id}{ext}")
        
        return patterns

    def get_format_directory(self, format: DiagramFormat) -> str:
        return format.value

    def validate_diagram_structure(self, data: dict, format: DiagramFormat) -> bool:
        if format == DiagramFormat.NATIVE:
            if not isinstance(data.get("nodes"), dict):
                raise ValueError("Native format requires 'nodes' to be a dictionary")
            return True
        
        elif format == DiagramFormat.LIGHT:
            required_fields = ["nodes", "connections", "persons"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Light format requires '{field}' field")
            if not isinstance(data.get("nodes"), list):
                raise ValueError("Light format requires 'nodes' to be a list")
            return True
        
        elif format == DiagramFormat.READABLE:
            if data.get("format") != "readable" and "readable" not in str(data):
                raise ValueError("Readable format should indicate its format type")
            return True
        
        return False