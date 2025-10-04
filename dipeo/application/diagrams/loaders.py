"""Diagram loading utilities."""

import json
from pathlib import Path
from typing import Any

import yaml

from dipeo.config import BASE_DIR
from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


class DiagramLoader:
    """Loads diagrams from various formats and locations."""

    def resolve_diagram_path(self, diagram: str, format_type: str | None = None) -> str:
        """Resolve diagram path based on name and format."""
        diagram_path = Path(diagram)

        # If absolute path and exists, return it
        if diagram_path.is_absolute() and diagram_path.exists():
            return str(diagram_path)

        # Try relative path
        if diagram_path.exists():
            return str(diagram_path.resolve())

        # If no extension, try adding format extension
        if not diagram_path.suffix and format_type:
            extensions = {
                "light": [".light.yml", ".light.yaml"],
                "native": [".json"],
                "readable": [".yaml", ".yml"],
            }

            for ext in extensions.get(format_type, []):
                # Try in various locations
                for base_dir in [
                    Path.cwd(),
                    BASE_DIR / "examples",
                    BASE_DIR / "examples/simple_diagrams",
                    BASE_DIR / "projects",
                    BASE_DIR / "files",
                ]:
                    test_path = base_dir / f"{diagram}{ext}"
                    if test_path.exists():
                        return str(test_path)

        # Try standard locations without format extension
        for base_dir in [
            Path.cwd(),
            BASE_DIR / "examples",
            BASE_DIR / "examples/simple_diagrams",
            BASE_DIR / "projects",
            BASE_DIR / "files",
        ]:
            test_path = base_dir / diagram
            if test_path.exists():
                return str(test_path)

            # Try with common extensions
            for ext in [".json", ".yaml", ".yml", ".light.yml", ".light.yaml"]:
                test_path = base_dir / f"{diagram}{ext}"
                if test_path.exists():
                    return str(test_path)

        # Return original if nothing found
        return diagram

    def load_diagram(self, file_path: str) -> dict[str, Any]:
        """Load a diagram from a file."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Diagram file not found: {file_path}")

        try:
            with open(path, encoding="utf-8") as f:
                if path.suffix == ".json":
                    return json.load(f)
                elif path.suffix in [".yaml", ".yml"]:
                    return yaml.safe_load(f)
                else:
                    # Try to detect format
                    content = f.read()
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return yaml.safe_load(content)
        except Exception as e:
            logger.error(f"Failed to load diagram from {file_path}: {e}")
            raise
