"""
Utility functions for the DiPeO CLI.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_API_KEY = "APIKEY_387B73"


class DiagramValidator:
    """Validates diagram structure using local models"""

    @staticmethod
    def validate_diagram(diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Validate diagram structure and apply defaults"""
        # Ensure all required fields exist with proper defaults
        if "nodes" not in diagram:
            diagram["nodes"] = {}
        if "arrows" not in diagram:
            diagram["arrows"] = {}
        if "handles" not in diagram:
            diagram["handles"] = {}
        if "persons" not in diagram:
            diagram["persons"] = {}
        if "apiKeys" not in diagram:
            diagram["apiKeys"] = {}

        # Add default API key if needed
        if not diagram["apiKeys"] and diagram["persons"]:
            diagram["apiKeys"][DEFAULT_API_KEY] = {
                "id": DEFAULT_API_KEY,
                "label": "Default API Key",
                "service": "openai",
                "key": "test-key",
                "masked_key": "***",
            }

        # Add metadata if missing
        if "metadata" not in diagram:
            diagram["metadata"] = {
                "name": "CLI Diagram",
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "version": "2.0.0",
            }

        return diagram


class DiagramLoader:
    """Handles loading and saving diagrams"""

    @staticmethod
    def load(file_path: str) -> Dict[str, Any]:
        """Load diagram from JSON or YAML file"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Diagram file not found: {file_path}")

        with open(file_path) as f:
            if path.suffix in [".yaml", ".yml"]:
                diagram = yaml.safe_load(f)
            else:
                diagram = json.load(f)

        return DiagramValidator.validate_diagram(diagram)

    @staticmethod
    def save(diagram: Dict[str, Any], file_path: str) -> None:
        """Save diagram to JSON or YAML file"""
        path = Path(file_path)

        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            if path.suffix in [".yaml", ".yml"]:
                yaml.dump(diagram, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(diagram, f, indent=2)
