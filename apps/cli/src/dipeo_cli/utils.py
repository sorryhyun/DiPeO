import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from dipeo_diagram import UnifiedDiagramConverter
from dipeo_domain import DomainDiagram, LLMService, NodeType


def to_graphql_format(diagram_dict: dict[str, Any]) -> dict[str, Any]:
    """Convert diagram from backend format to GraphQL format (lists).
    
    It handles both dict-of-dicts format and list format.
    """
    # If already in list format, return as-is
    if all(
        isinstance(diagram_dict.get(field), list)
        for field in ["nodes", "arrows", "handles", "persons"]
        if field in diagram_dict
    ):
        return diagram_dict
    
    # Convert dict-of-dicts to lists
    result = diagram_dict.copy()
    
    for field in ["nodes", "arrows", "handles", "persons"]:
        if field in result and isinstance(result[field], dict):
            result[field] = list(result[field].values())
    
    # Handle API keys (both camelCase and snake_case)
    if "apiKeys" in result and isinstance(result["apiKeys"], dict):
        result["api_keys"] = list(result["apiKeys"].values())
        del result["apiKeys"]
    elif "api_keys" in result and isinstance(result["api_keys"], dict):
        result["api_keys"] = list(result["api_keys"].values())
    
    return result


def ensure_diagram_defaults(diagram: dict[str, Any]) -> dict[str, Any]:
    """Ensure diagram has all required fields with defaults.
    
    This function prepares a raw diagram dict for use by ensuring
    all required fields exist with appropriate defaults.
    """
    # Ensure all required fields exist
    diagram.setdefault("nodes", [] if isinstance(diagram.get("nodes"), list) else list(diagram.get("nodes", {}).values()))
    diagram.setdefault("arrows", [] if isinstance(diagram.get("arrows"), list) else list(diagram.get("arrows", {}).values()))
    diagram.setdefault("handles", [] if isinstance(diagram.get("handles"), list) else list(diagram.get("handles", {}).values()))
    diagram.setdefault("persons", [] if isinstance(diagram.get("persons"), list) else list(diagram.get("persons", {}).values()))
    
    # Handle both camelCase and snake_case for API keys
    if "apiKeys" in diagram and "api_keys" not in diagram:
        diagram["api_keys"] = diagram.pop("apiKeys")
    
    # Ensure api_keys is a list
    api_keys = diagram.get("api_keys", [])
    if isinstance(api_keys, dict):
        api_keys = list(api_keys.values())
    diagram["api_keys"] = api_keys
    
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
    def load(file_path: str, format_id: str | None = None) -> dict[str, Any]:
        """Load diagram from JSON or YAML file
        
        Args:
            file_path: Path to the diagram file
            format_id: Optional format specification ('native', 'light', 'readable')
                      If not provided, format is auto-detected
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Diagram file not found: {file_path}")

        # If format is specified, use UnifiedDiagramConverter
        if format_id:
            converter = UnifiedDiagramConverter()
            with open(file_path) as f:
                content = f.read()
            domain_diagram = converter.deserialize(content, format_id)
            # Convert domain model to dict using model_dump
            diagram = domain_diagram.model_dump(mode='json', by_alias=True)
        else:
            # Auto-detect format from file extension
            with open(file_path) as f:
                if path.suffix in [".yaml", ".yml"]:
                    diagram = yaml.safe_load(f)
                else:
                    diagram = json.load(f)

        return ensure_diagram_defaults(diagram)

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


# Utility functions for working with generated models


def diagram_to_dict(diagram: DomainDiagram) -> dict[str, Any]:
    """Convert a diagram to dictionary for JSON serialization.

    Uses Pydantic's model_dump() method.
    """
    # Convert to dict using Pydantic's method
    return diagram.model_dump(by_alias=True)


# Validation helpers
def validate_node_type(node_type: str) -> bool:
    try:
        NodeType(node_type)
        return True
    except ValueError:
        return False


def validate_llm_service(service: str) -> bool:
    try:
        LLMService(service)
        return True
    except ValueError:
        return False
