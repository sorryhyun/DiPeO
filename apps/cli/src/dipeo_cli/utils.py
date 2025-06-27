
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

DEFAULT_API_KEY = "APIKEY_387B73"


class DiagramConverter:
    """Converts diagram between different formats for API compatibility"""

    @staticmethod
    def dict_to_list(mapping: dict[str, Any]) -> list[Any]:
        return [
            ({**value, "id": key} if isinstance(value, dict) and "id" not in value else value)
            for key, value in mapping.items()
        ]

    @staticmethod
    def list_to_dict(items: list[Any]) -> dict[str, Any]:
        if isinstance(items, dict):
            return items
        return {item["id"]: item for item in items if isinstance(item, dict) and "id" in item}

    @classmethod
    def to_graphql_format(cls, diagram: dict[str, Any]) -> dict[str, Any]:
        """Convert diagram from file format to GraphQL format (lists)."""
        result = diagram.copy()

        # Convert dict fields to lists
        for field in ["nodes", "arrows", "handles", "persons"]:
            if field in result and isinstance(result[field], dict):
                result[field] = cls.dict_to_list(result[field])

        # Handle API keys with both camelCase and snake_case
        if "apiKeys" in result and isinstance(result["apiKeys"], dict):
            result["apiKeys"] = cls.dict_to_list(result["apiKeys"])
        elif "api_keys" in result and isinstance(result["api_keys"], dict):
            result["apiKeys"] = cls.dict_to_list(result["api_keys"])
            del result["api_keys"]

        return result


class DiagramValidator:
    """Validates diagram structure using local models"""

    @staticmethod
    def validate_diagram(diagram: dict[str, Any]) -> dict[str, Any]:
        """Validate diagram structure and apply defaults"""
        # Ensure all required fields exist with proper defaults
        if "nodes" not in diagram:
            diagram["nodes"] = {} if not isinstance(diagram.get("nodes"), list) else diagram["nodes"]
        if "arrows" not in diagram:
            diagram["arrows"] = {} if not isinstance(diagram.get("arrows"), list) else diagram["arrows"]
        if "handles" not in diagram:
            diagram["handles"] = {} if not isinstance(diagram.get("handles"), list) else diagram["handles"]
        if "persons" not in diagram:
            diagram["persons"] = {} if not isinstance(diagram.get("persons"), list) else diagram["persons"]
        # Handle both camelCase and snake_case for API keys
        if "apiKeys" not in diagram and "api_keys" not in diagram:
            diagram["apiKeys"] = {}
        elif "api_keys" in diagram and "apiKeys" not in diagram:
            # Convert snake_case to camelCase for consistency
            diagram["apiKeys"] = diagram.pop("api_keys", {})

        # Add default API key if needed
        api_keys = diagram.get("apiKeys", {})
        if isinstance(api_keys, list):
            api_keys = {k["id"]: k for k in api_keys}
            diagram["apiKeys"] = api_keys

        if not api_keys and diagram["persons"]:
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
    def load(file_path: str) -> dict[str, Any]:
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
    def save(diagram: dict[str, Any], file_path: str) -> None:
        """Save diagram to JSON or YAML file"""
        path = Path(file_path)

        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            if path.suffix in [".yaml", ".yml"]:
                yaml.dump(diagram, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(diagram, f, indent=2)
