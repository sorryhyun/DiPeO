"""Protocol definition for diagram operations - single source of truth."""

import logging
from typing import (
    Protocol,
    runtime_checkable,
    Optional,
)

logger = logging.getLogger(__name__)

from dipeo.diagram_generated import DiagramFormat, DomainDiagram
from dipeo.domain.ports.storage import DiagramInfo
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram


@runtime_checkable
class DiagramPort(Protocol):
    """Protocol for all diagram operations - single source of truth.
    
    This interface provides:
    - CRUD operations (create, get, update, delete)
    - Loading operations (from file or string)
    - Format operations (detect, serialize/deserialize)
    - Compilation (compile to ExecutableDiagram)
    - Query operations (exists, list)
    """

    # Format operations
    def detect_format(self, content: str) -> DiagramFormat:
        """Detect the format of diagram content."""
        ...
    
    def serialize(self, diagram: DomainDiagram, format_type: str) -> str:
        """Serialize a DomainDiagram to string."""
        ...
    
    def deserialize(self, content: str, format_type: Optional[str] = None) -> DomainDiagram:
        """Deserialize string content to DomainDiagram."""
        ...
    
    def load_from_string(self, content: str, format_type: Optional[str] = None) -> DomainDiagram:
        """Load a diagram from string content."""
        ...

    # File operations
    async def load_from_file(self, file_path: str) -> DomainDiagram:
        """Load diagram from file."""
        ...
    
    # Query operations
    async def exists(self, diagram_id: str) -> bool:
        """Check if a diagram exists."""
        ...
    
    async def list_diagrams(self, format_type: Optional[str] = None) -> list[DiagramInfo]:
        """List all diagrams, optionally filtered by format."""
        ...
    
    # CRUD operations
    async def create_diagram(
        self, name: str, diagram: DomainDiagram, format_type: str = "native"
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
        
    async def get_diagram(self, diagram_id: str) -> DomainDiagram | None: 
        """Get a diagram by its ID.
        
        Returns:
            DomainDiagram if found, None otherwise
        """
        ...
        
    async def update_diagram(self, diagram_id: str, diagram: DomainDiagram) -> None: 
        """Update an existing diagram."""
        ...
        
    async def delete_diagram(self, diagram_id: str) -> None: 
        """Delete a diagram from storage."""
        ...
    
    # Compilation
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile a DomainDiagram to ExecutableDiagram.
        
        Args:
            domain_diagram: The diagram to compile
            
        Returns:
            ExecutableDiagram: The compiled diagram ready for execution
        """
        ...


