"""Domain service for diagram format detection and validation."""

import json

import yaml

from dipeo.models import DiagramFormat


class DiagramFormatService:
    """
    Domain service that encapsulates business logic for diagram format operations.
    This includes format detection, validation, and format-specific rules.
    """

    def detect_format(self, content: str) -> DiagramFormat:
        """
        Detect the format of a diagram from its content.
        This is pure business logic without any I/O operations.
        """
        content = content.strip()

        # Check for JSON format
        if content.startswith('{'):
            try:
                data = json.loads(content)
                if "nodes" in data and isinstance(data["nodes"], dict):
                    return DiagramFormat.NATIVE
                return DiagramFormat.NATIVE
            except json.JSONDecodeError:
                pass

        # Check for YAML formats
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                # Check for light format
                if (data.get("version") == "light" or
                        (isinstance(data.get("nodes"), list) and
                         "connections" in data and
                         "persons" in data)):
                    return DiagramFormat.LIGHT
                # Check for readable format
                if data.get("format") == "readable":
                    return DiagramFormat.READABLE
                # Default YAML is light format
                return DiagramFormat.LIGHT
        except yaml.YAMLError:
            pass

        raise ValueError("Unable to detect diagram format")

    def validate_format(self, content: str, format: DiagramFormat) -> bool:
        """
        Validate that content matches the expected format.
        Returns True if valid, raises ValueError if invalid.
        """
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
        """
        Determine the likely format based on filename patterns.
        This is a business rule about naming conventions.
        """
        # Check for new extension format
        if filename.endswith(".native.json"):
            return DiagramFormat.NATIVE
        elif filename.endswith(".light.yaml") or filename.endswith(".light.yml"):
            return DiagramFormat.LIGHT
        elif filename.endswith(".readable.yaml") or filename.endswith(".readable.yml"):
            return DiagramFormat.READABLE
        # Backward compatibility with old format
        elif filename.endswith(".json"):
            return DiagramFormat.NATIVE
        elif filename.endswith((".yaml", ".yml")):
            # Check for format hints in filename
            if "light" in filename.lower():
                return DiagramFormat.LIGHT
            elif "readable" in filename.lower():
                return DiagramFormat.READABLE
            # Default YAML format
            return DiagramFormat.LIGHT
        return None

    def get_file_extension_for_format(self, format: DiagramFormat) -> str:
        """
        Get the preferred file extension for a given format.
        This is a business rule about file naming conventions.
        """
        if format == DiagramFormat.NATIVE:
            return ".native.json"
        elif format == DiagramFormat.LIGHT:
            return ".light.yaml"
        elif format == DiagramFormat.READABLE:
            return ".readable.yaml"
        else:
            return ".light.yaml"  # Default

    def construct_search_patterns(
        self, diagram_id: str, formats: list | None = None
    ) -> list:
        """
        Construct search patterns for finding a diagram by ID.
        This encodes business rules about where diagrams might be stored.
        """
        if formats is None:
            formats = [DiagramFormat.NATIVE, DiagramFormat.LIGHT, DiagramFormat.READABLE]
        
        patterns = []
        
        # New extension format patterns
        for format in formats:
            ext = self.get_file_extension_for_format(format)
            # Direct match with new extension
            patterns.append(f"{diagram_id}{ext}")
            # Also check in format directories for backward compatibility
            patterns.append(f"{format.value}/{diagram_id}{ext}")
        
        # Backward compatibility patterns
        old_extensions = [".yaml", ".yml", ".json"]
        for format in formats:
            format_dir = format.value
            for ext in old_extensions:
                patterns.append(f"{format_dir}/{diagram_id}{ext}")
        
        # Also check old extensions without format directory
        for ext in old_extensions:
            patterns.append(f"{diagram_id}{ext}")
        
        return patterns

    def get_format_directory(self, format: DiagramFormat) -> str:
        """
        Get the directory name for a given format.
        This is a business rule about directory structure.
        """
        return format.value

    def validate_diagram_structure(self, data: dict, format: DiagramFormat) -> bool:
        """
        Validate that a diagram data structure matches format requirements.
        This encodes business rules about what makes a valid diagram.
        """
        if format == DiagramFormat.NATIVE:
            # Native format must have nodes as a dict
            if not isinstance(data.get("nodes"), dict):
                raise ValueError("Native format requires 'nodes' to be a dictionary")
            return True
        
        elif format == DiagramFormat.LIGHT:
            # Light format requirements
            required_fields = ["nodes", "connections", "persons"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Light format requires '{field}' field")
            if not isinstance(data.get("nodes"), list):
                raise ValueError("Light format requires 'nodes' to be a list")
            return True
        
        elif format == DiagramFormat.READABLE:
            # Readable format is more flexible but should have format indicator
            if data.get("format") != "readable" and "readable" not in str(data):
                raise ValueError("Readable format should indicate its format type")
            return True
        
        return False