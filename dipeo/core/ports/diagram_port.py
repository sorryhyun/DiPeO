# Infrastructure implementation for diagram file I/O operations.

import json
import logging
from pathlib import Path
from typing import Any

import yaml
from dipeo.core.constants import BASE_DIR
from dipeo.utils.diagram import DiagramBusinessLogic as DiagramDomainService

logger = logging.getLogger(__name__)

from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
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
            format: Optional[DiagramFormat] = None,
    ) -> DomainDiagram: ...

    async def load_from_file(
            self,
            file_path: str,
            format: Optional[DiagramFormat] = None,
    ) -> DomainDiagram: ...
    def list_diagrams(self, directory: Optional[str] = None) -> List[Dict[str, Any]]: ...
    def save_diagram(self, path: str, diagram: Dict[str, Any]) -> None: ...
    def create_diagram(
        self, name: str, diagram: Dict[str, Any], format: str = "json"
    ) -> str: ...
    def update_diagram(self, path: str, diagram: Dict[str, Any]) -> None: ...
    def delete_diagram(self, path: str) -> None: ...
    async def save_diagram_with_id(
        self, diagram_dict: Dict[str, Any], filename: str
    ) -> str: ...
    async def get_diagram(self, diagram_id: str) -> Optional[Dict[str, Any]]: ...


