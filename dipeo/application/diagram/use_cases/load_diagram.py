"""Use case for loading diagrams from various sources."""

from pathlib import Path
from typing import Any, ClassVar

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.segregated_ports import DiagramFilePort, DiagramFormatPort

logger = get_module_logger(__name__)


class LoadDiagramUseCase:
    """Loads diagrams from files or inline data with format detection and caching."""

    FORMAT_MAP: ClassVar = {
        "light": ".light.yaml",
        "native": ".native.json",
        "readable": ".readable.yaml",
    }

    def __init__(self, file_port: DiagramFilePort, format_port: DiagramFormatPort | None = None):
        self._file_port = file_port
        self._format_port = format_port
        self._diagram_cache: dict[str, DomainDiagram] = {}

    async def load_diagram(
        self,
        diagram_name: str | None = None,
        diagram_format: str | None = None,
        diagram_data: dict[str, Any] | None = None,
    ) -> DomainDiagram:
        """Load diagram from name/format or inline data.

        Args:
            diagram_name: Name or path of the diagram to load
            diagram_format: Format of the diagram ('light', 'native', 'readable')
            diagram_data: Inline diagram data (if not loading from file)

        Returns:
            DomainDiagram loaded from the specified source

        Raises:
            ValueError: If neither diagram_name nor diagram_data is provided
        """
        if diagram_data is not None:
            logger.debug("Loading diagram from inline data")
            return await self._load_from_data(diagram_data)

        if diagram_name is None:
            raise ValueError("Either diagram_name or diagram_data must be provided")

        cache_key = f"{diagram_name}:{diagram_format or 'auto'}"
        if cache_key in self._diagram_cache:
            logger.debug(f"Returning cached diagram for {cache_key}")
            return self._diagram_cache[cache_key]

        file_path = self._construct_file_path(diagram_name, diagram_format)

        logger.debug(f"Loading diagram from file: {file_path}")

        if hasattr(self._file_port, "initialize"):
            await self._file_port.initialize()

        diagram = await self._file_port.load_from_file(str(file_path))

        self._diagram_cache[cache_key] = diagram

        return diagram

    def construct_diagram_path(self, diagram_name: str, diagram_format: str | None = None) -> str:
        """Construct the file path for a diagram.

        Path construction rules:
        - projects/* -> projects/{name}{suffix}
        - codegen/* -> files/{name}{suffix}
        - examples/* -> examples/{name}{suffix}
        - others -> examples/{name}{suffix}

        Args:
            diagram_name: Name or partial path of the diagram
            diagram_format: Optional format specification

        Returns:
            Path to the diagram file as string
        """
        if "." in Path(diagram_name).name:
            return str(diagram_name)

        format_suffix = self.FORMAT_MAP.get(diagram_format or "light", ".light.yaml")

        if diagram_name.startswith("projects/"):
            file_path = f"{diagram_name}{format_suffix}"
        elif diagram_name.startswith("codegen/"):
            file_path = f"files/{diagram_name}{format_suffix}"
        elif diagram_name.startswith("examples/"):
            file_path = f"{diagram_name}{format_suffix}"
        else:
            file_path = f"examples/{diagram_name}{format_suffix}"

        return file_path

    def _construct_file_path(self, diagram_name: str, diagram_format: str | None = None) -> Path:
        """Construct file path as Path object."""
        return Path(self.construct_diagram_path(diagram_name, diagram_format))

    async def _load_from_data(self, data: dict[str, Any]) -> DomainDiagram:
        """Load diagram from inline data."""
        if self._format_port and hasattr(data, "get"):
            import json

            content = json.dumps(data)
            return self._format_port.deserialize(content, "native")

        return DomainDiagram(**data)

    def clear_cache(self) -> None:
        """Clear the diagram cache."""
        self._diagram_cache.clear()
        logger.debug("Diagram cache cleared")
