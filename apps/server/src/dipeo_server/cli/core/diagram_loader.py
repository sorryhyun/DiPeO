"""Diagram loading and path resolution utilities."""

import json
from pathlib import Path
from typing import Any

import yaml

from dipeo.config import BASE_DIR
from dipeo.config.base_logger import get_module_logger
from dipeo.infrastructure.diagram.adapters import UnifiedSerializerAdapter

logger = get_module_logger(__name__)


class DiagramLoader:
    """Handles loading diagrams from various sources and formats."""

    def __init__(self):
        """Initialize diagram loader."""
        self.serializer = None

    async def initialize(self):
        """Initialize the serializer."""
        self.serializer = UnifiedSerializerAdapter()
        await self.serializer.initialize()

    async def load_diagram(
        self, diagram: str, format_type: str | None
    ) -> tuple[dict[str, Any], str]:
        """Load diagram from file.

        Returns:
            Tuple of (diagram_data, diagram_path)
        """
        diagram_path = self.resolve_diagram_path(diagram, format_type)

        with open(diagram_path, encoding="utf-8") as f:
            if diagram_path.endswith(".json"):
                diagram_data = json.load(f)
            else:
                diagram_data = yaml.safe_load(f)

        return diagram_data, diagram_path

    async def load_and_deserialize(
        self, diagram: str, format_type: str | None
    ) -> tuple[Any, dict[str, Any], str]:
        """Load and deserialize diagram to domain model.

        Returns:
            Tuple of (domain_diagram, diagram_data, diagram_path)
        """
        if not self.serializer:
            await self.initialize()

        diagram_data, diagram_path = await self.load_diagram(diagram, format_type)

        format_hint = format_type or "native"
        if format_hint in ["light", "readable"]:
            content = yaml.dump(diagram_data, default_flow_style=False, sort_keys=False)
            domain_diagram = self.serializer.deserialize_from_storage(
                content, format_hint, diagram_path
            )
        else:
            json_content = json.dumps(diagram_data)
            domain_diagram = self.serializer.deserialize_from_storage(
                json_content, "native", diagram_path
            )

        return domain_diagram, diagram_data, diagram_path

    def resolve_diagram_path(self, diagram: str, format_type: str | None) -> str:
        """Resolve diagram path based on name and format."""
        diagram_path = Path(diagram)

        if diagram_path.is_absolute() and diagram_path.exists():
            return str(diagram_path)

        if diagram_path.exists():
            return str(diagram_path.resolve())

        if not diagram_path.suffix and format_type:
            extensions = {
                "light": [".light.yml", ".light.yaml"],
                "native": [".json"],
                "readable": [".yaml", ".yml"],
            }

            for ext in extensions.get(format_type, []):
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

            for ext in [".json", ".yaml", ".yml", ".light.yml", ".light.yaml"]:
                test_path = base_dir / f"{diagram}{ext}"
                if test_path.exists():
                    return str(test_path)

        return diagram

    def detect_format(self, file_path: str) -> str:
        """Detect diagram format from file extension."""
        path = Path(file_path)
        if path.suffix in [".yml", ".yaml"]:
            with open(path) as f:
                content = f.read()
                if "nodes:" in content and "edges:" in content:
                    return "light"
                else:
                    return "readable"
        elif path.suffix == ".json":
            return "native"
        else:
            return "native"
