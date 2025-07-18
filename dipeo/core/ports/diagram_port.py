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
    """Protocol for diagram operations.
    
    Note: All I/O operations are async to support non-blocking execution.
    Format detection and in-memory operations remain synchronous.
    """

    def detect_format(self, content: str) -> DiagramFormat: 
        """Detect the format of diagram content."""
        ...
        
    def load_diagram(
            self,
            content: str,
            format: DiagramFormat | None = None,
    ) -> DomainDiagram: 
        """Load a diagram from string content."""
        ...

    async def load_from_file(
            self,
            file_path: str,
            format: DiagramFormat | None = None,
    ) -> DomainDiagram: 
        """Load a diagram from a file."""
        ...
        
    async def list_diagrams(self, directory: str | None = None) -> list[dict[str, Any]]: 
        """List all available diagrams."""
        ...
        
    async def save_diagram(self, path: str, diagram: dict[str, Any]) -> None: 
        """Save a diagram to a file."""
        ...
        
    async def create_diagram(
        self, name: str, diagram: dict[str, Any], format: str = "json"
    ) -> str: 
        """Create a new diagram with a unique filename."""
        ...
        
    async def update_diagram(self, path: str, diagram: dict[str, Any]) -> None: 
        """Update an existing diagram."""
        ...
        
    async def delete_diagram(self, path: str) -> None: 
        """Delete a diagram file."""
        ...
        
    async def save_diagram_with_id(
        self, diagram_dict: dict[str, Any], filename: str
    ) -> str: 
        """Save a diagram ensuring it has an ID."""
        ...
        
    async def get_diagram(self, diagram_id: str) -> dict[str, Any] | None: 
        """Get a diagram by its ID."""
        ...


