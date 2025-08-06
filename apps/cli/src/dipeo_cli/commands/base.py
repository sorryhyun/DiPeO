"""Base utilities for CLI commands."""

import json
from pathlib import Path
from typing import Any

import yaml
from dipeo.core.constants import FILES_DIR


class DiagramLoader:
    """Utilities for loading and resolving diagram paths."""

    @staticmethod
    def resolve_diagram_path(diagram: str, format_type: str | None = None) -> str:
        """Resolve diagram path based on format type."""
        # If it's an absolute path, use as-is
        path = Path(diagram)
        if path.is_absolute():
            return diagram

        # If it has a file extension, check if it exists
        if diagram.endswith((".native.json", ".light.yaml", ".readable.yaml")):
            # Check if it exists as-is
            if Path(diagram).exists():
                return diagram
            # Try with files/ prefix
            path_with_files = FILES_DIR / diagram
            if path_with_files.exists():
                return str(path_with_files)
            # If it starts with files/, also try resolving from project root
            if diagram.startswith("files/"):
                return str(FILES_DIR.parent / diagram)

        # For paths without extension, auto-prepend files/ if not present
        diagram_path = diagram[6:] if diagram.startswith("files/") else diagram

        if not format_type:
            # Try to find the diagram with known extensions
            extensions = [".native.json", ".light.yaml", ".readable.yaml"]

            for ext in extensions:
                path = FILES_DIR / f"{diagram_path}{ext}"
                if path.exists():
                    return str(path)

            raise FileNotFoundError(f"Diagram '{diagram}' not found in any format")

        # Use specified format
        format_map = {
            "light": ".light.yaml",
            "native": ".native.json",
            "readable": ".readable.yaml",
        }

        ext = format_map.get(format_type)
        if not ext:
            raise ValueError(f"Unknown format type: {format_type}")

        path = FILES_DIR / f"{diagram_path}{ext}"
        return str(path)

    @staticmethod
    def load_diagram(file_path: str) -> dict[str, Any]:
        """Load diagram from file (JSON or YAML)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Diagram file not found: {file_path}")

        with path.open(encoding="utf-8") as f:
            content = f.read()

        # Parse based on extension
        if str(path).endswith((".light.yaml", ".readable.yaml")):
            return yaml.safe_load(content)
        if str(path).endswith(".native.json"):
            return json.loads(content)
        raise ValueError(f"Unknown diagram file format: {file_path}")

    @staticmethod
    def get_diagram_format(diagram_path: str) -> str:
        """Determine diagram format from file path."""
        if diagram_path.endswith(".light.yaml"):
            return "light"
        if diagram_path.endswith(".readable.yaml"):
            return "readable"
        return "native"

    @staticmethod
    def get_diagram_name(diagram_path: str) -> str:
        """Extract diagram name from path for browser URL."""
        path = Path(diagram_path)
        try:
            # Try to make path relative to FILES_DIR
            relative_path = path.relative_to(FILES_DIR)
            # Remove format suffix from the relative path
            path_str = str(relative_path)
            for suffix in [".native.json", ".light.yaml", ".readable.yaml"]:
                if path_str.endswith(suffix):
                    path_str = path_str[: -len(suffix)]
                    break
            return path_str
        except ValueError:
            # If not under FILES_DIR, use the original logic
            name = path.name
            for suffix in [".native.json", ".light.yaml", ".readable.yaml"]:
                if name.endswith(suffix):
                    name = name[: -len(suffix)]
                    break
            return name
