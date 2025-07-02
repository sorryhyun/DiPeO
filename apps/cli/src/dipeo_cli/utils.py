import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from dipeo_diagram import UnifiedDiagramConverter
from dipeo_domain import DomainDiagram




def ensure_diagram_defaults(diagram: dict[str, Any]) -> dict[str, Any]:
    """Ensure diagram has all required fields with defaults.
    
    This function prepares a raw diagram dict for use by ensuring
    all required fields exist with appropriate defaults.
    """
    # Ensure all required fields exist as lists
    diagram.setdefault("nodes", [])
    diagram.setdefault("arrows", [])
    diagram.setdefault("handles", [])
    diagram.setdefault("persons", [])
    diagram.setdefault("api_keys", [])
    
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
        """Load diagram from JSON or YAML file using UnifiedDiagramConverter
        
        Args:
            file_path: Path to the diagram file
            format_id: Optional format specification ('native', 'light', 'readable')
                      If not provided, format is auto-detected by converter
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Diagram file not found: {file_path}")

        # Always use UnifiedDiagramConverter
        converter = UnifiedDiagramConverter()
        with open(file_path) as f:
            content = f.read()
        
        # Deserialize with optional format hint
        domain_diagram = converter.deserialize(content, format_id)
        
        # Convert domain model to dict using model_dump
        diagram = domain_diagram.model_dump(mode='json', by_alias=True)

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




