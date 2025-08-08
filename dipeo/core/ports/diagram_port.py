"""Protocol definition for diagram I/O operations."""

import logging
from typing import (
    Any,
    Protocol,
    runtime_checkable,
)

logger = logging.getLogger(__name__)

from dipeo.diagram_generated import DiagramFormat, DomainDiagram


@runtime_checkable
class DiagramPort(Protocol):
    """Protocol for diagram operations. I/O operations are async."""

    def detect_format(self, content: str) -> DiagramFormat:
        ...
        
    def load_diagram(
            self,
            content: str,
            format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        ...

    async def load_from_file(
            self,
            file_path: str,
            format: DiagramFormat | None = None,
    ) -> DomainDiagram:
        ...
        
    async def list_diagrams(self, directory: str | None = None) -> list[dict[str, Any]]:
        ...
        
    async def save_diagram(self, diagram_id: str, diagram: DomainDiagram) -> None:
        """Save a DomainDiagram to storage."""
        ...
        
    async def create_diagram(
        self, name: str, diagram: DomainDiagram, format: str = "native"
    ) -> str: 
        """Create a new diagram with a unique ID.
        
        Args:
            name: Base name for the diagram
            diagram: The DomainDiagram to save
            format: Storage format (native, light, readable)
            
        Returns:
            The unique diagram ID assigned
        """
        ...
        
    async def update_diagram(self, diagram_id: str, diagram: DomainDiagram) -> None: 
        """Update an existing diagram."""
        ...
        
    async def delete_diagram(self, diagram_id: str) -> None: 
        """Delete a diagram from storage."""
        ...
        
    async def get_diagram(self, diagram_id: str) -> DomainDiagram | None: 
        """Get a diagram by its ID.
        
        Returns:
            DomainDiagram if found, None otherwise
        """
        ...


