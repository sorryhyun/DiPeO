# Protocol definition for diagram I/O operations.

import logging
from typing import Any

logger = logging.getLogger(__name__)

from typing import (
    Protocol,
    runtime_checkable,
)

from dipeo.models import DiagramFormat, DomainDiagram


@runtime_checkable
class DiagramPort(Protocol):
    """Protocol for diagram operations."""

    def detect_format(self, content: str) -> DiagramFormat: ...
    def load_diagram(
            self,
            content: str,
            format: DiagramFormat | None = None,
    ) -> DomainDiagram: ...

    async def load_from_file(
            self,
            file_path: str,
            format: DiagramFormat | None = None,
    ) -> DomainDiagram: ...
    def list_diagrams(self, directory: str | None = None) -> list[dict[str, Any]]: ...
    def save_diagram(self, path: str, diagram: dict[str, Any]) -> None: ...
    def create_diagram(
        self, name: str, diagram: dict[str, Any], format: str = "json"
    ) -> str: ...
    def update_diagram(self, path: str, diagram: dict[str, Any]) -> None: ...
    def delete_diagram(self, path: str) -> None: ...
    async def save_diagram_with_id(
        self, diagram_dict: dict[str, Any], filename: str
    ) -> str: ...
    async def get_diagram(self, diagram_id: str) -> dict[str, Any] | None: ...


