"""Domain service for diagram format detection and validation."""

import json
import yaml
from typing import Optional

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
                    return DiagramFormat.native
                return DiagramFormat.native
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
                    return DiagramFormat.light
                # Check for readable format
                if data.get("format") == "readable":
                    return DiagramFormat.readable
                # Default YAML is light format
                return DiagramFormat.light
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
            raise ValueError(f"Invalid {format.value} format: {str(e)}")

    def determine_format_from_filename(self, filename: str) -> Optional[DiagramFormat]:
        """
        Determine the likely format based on filename patterns.
        This is a business rule about naming conventions.
        """
        if filename.endswith(".json"):
            return DiagramFormat.native
        elif filename.endswith((".yaml", ".yml")):
            # Check for format hints in filename
            if "light" in filename.lower():
                return DiagramFormat.light
            elif "readable" in filename.lower():
                return DiagramFormat.readable
            # Default YAML format
            return DiagramFormat.light
        return None

    def get_file_extension_for_format(self, format: DiagramFormat) -> str:
        """
        Get the preferred file extension for a given format.
        This is a business rule about file naming conventions.
        """
        if format == DiagramFormat.native:
            return ".json"
        elif format in [DiagramFormat.light, DiagramFormat.readable]:
            return ".yaml"
        else:
            return ".yaml"  # Default

    def construct_search_patterns(
        self, diagram_id: str, formats: Optional[list] = None
    ) -> list:
        """
        Construct search patterns for finding a diagram by ID.
        This encodes business rules about where diagrams might be stored.
        """
        if formats is None:
            formats = [DiagramFormat.native, DiagramFormat.light, DiagramFormat.readable]
        
        patterns = []
        extensions = [".yaml", ".yml", ".json"]
        
        for format in formats:
            format_dir = format.value
            for ext in extensions:
                # Direct ID match
                patterns.append(f"{format_dir}/{diagram_id}{ext}")
                # ID might be the filename without extension
                patterns.append(f"{format_dir}/{diagram_id}")
        
        # Also check without format directory
        for ext in extensions:
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
        if format == DiagramFormat.native:
            # Native format must have nodes as a dict
            if not isinstance(data.get("nodes"), dict):
                raise ValueError("Native format requires 'nodes' to be a dictionary")
            return True
        
        elif format == DiagramFormat.light:
            # Light format requirements
            required_fields = ["nodes", "connections", "persons"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Light format requires '{field}' field")
            if not isinstance(data.get("nodes"), list):
                raise ValueError("Light format requires 'nodes' to be a list")
            return True
        
        elif format == DiagramFormat.readable:
            # Readable format is more flexible but should have format indicator
            if data.get("format") != "readable" and "readable" not in str(data):
                raise ValueError("Readable format should indicate its format type")
            return True
        
        return False