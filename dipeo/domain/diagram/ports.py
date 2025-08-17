"""Domain ports for diagram compilation and conversion.

This module defines the domain-owned contracts for diagram operations,
moving them from core/ports to domain ownership.
"""

from typing import Protocol, TYPE_CHECKING, Any, Optional
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from dipeo.diagram_generated import DomainDiagram, DiagramFormat
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
    from dipeo.domain.storage import DiagramInfo


# ============================================================================
# Diagram Compilation Port
# ============================================================================

class DiagramCompiler(Protocol):
    """Protocol for compiling between different diagram representations.
    
    This is the domain-owned contract for diagram compilation.
    Implementations transform DomainDiagram to ExecutableDiagram.
    """
    
    def compile(self, domain_diagram: "DomainDiagram") -> "ExecutableDiagram":
        """Compile domain diagram to executable form with resolved connections and execution order."""
        ...


# ============================================================================
# Diagram Storage Serialization Port
# ============================================================================

class DiagramStorageSerializer(ABC):
    """Interface for serializing diagrams to/from storage formats.
    
    This is used ONLY for file persistence. Internal APIs should
    pass DomainDiagram objects directly.
    """
    
    @abstractmethod
    def serialize_for_storage(self, diagram: "DomainDiagram", format: str) -> str:
        """Serialize a DomainDiagram to string for file storage.
        
        Args:
            diagram: The DomainDiagram to serialize
            format: Target format ('json', 'yaml', 'light', 'readable')
            
        Returns:
            String representation for file storage
        """
        pass

    @abstractmethod
    def deserialize_from_storage(self, content: str, format: str | None = None) -> "DomainDiagram":
        """Deserialize file content to DomainDiagram.
        
        Args:
            content: String content from file
            format: Optional format hint, will auto-detect if not provided
            
        Returns:
            DomainDiagram instance
        """
        pass
    
    def validate(self, content: str) -> tuple[bool, list[str]]:
        """Validate that content can be deserialized."""
        try:
            self.deserialize_from_storage(content)
            return True, []
        except Exception as e:
            return False, [str(e)]


# ============================================================================
# Format Strategy Port
# ============================================================================

class FormatStrategy(ABC):
    """Strategy for handling specific diagram formats.
    
    Each format (light, native, readable) has its own strategy.
    """
    
    @abstractmethod
    def parse(self, content: str) -> Any:
        """Parse content to intermediate format (dict, Pydantic model, etc)."""
        pass

    @abstractmethod
    def format(self, data: Any) -> str:
        """Format data to string representation."""
        pass

    @abstractmethod
    def deserialize_to_domain(self, content: str) -> "DomainDiagram":
        """Deserialize format-specific string to domain diagram."""
        pass

    @abstractmethod
    def serialize_from_domain(self, diagram: "DomainDiagram") -> str:
        """Serialize domain diagram to format-specific string."""
        pass

    @abstractmethod
    def detect_confidence(self, data: dict[str, Any]) -> float:
        """Detect confidence that data matches this format."""
        pass

    @property
    @abstractmethod
    def format_id(self) -> str:
        """Get format identifier."""
        pass

    @property
    @abstractmethod
    def format_info(self) -> dict[str, str]:
        """Get format information."""
        pass

    def quick_match(self, content: str) -> bool:
        """Quick check if content matches format."""
        try:
            self.parse(content)
            return True
        except Exception:
            return False


# ============================================================================
# Unified Diagram Port
# ============================================================================

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
    def detect_format(self, content: str) -> "DiagramFormat":
        """Detect the format of diagram content."""
        ...
    
    def serialize(self, diagram: "DomainDiagram", format_type: str) -> str:
        """Serialize a DomainDiagram to string."""
        ...
    
    def deserialize(self, content: str, format_type: Optional[str] = None) -> "DomainDiagram":
        """Deserialize string content to DomainDiagram."""
        ...
    
    def load_from_string(self, content: str, format_type: Optional[str] = None) -> "DomainDiagram":
        """Load a diagram from string content."""
        ...

    # File operations
    async def load_from_file(self, file_path: str) -> "DomainDiagram":
        """Load diagram from file."""
        ...
    
    # Query operations
    async def exists(self, diagram_id: str) -> bool:
        """Check if a diagram exists."""
        ...
    
    async def list_diagrams(self, format_type: Optional[str] = None) -> list["DiagramInfo"]:
        """List all diagrams, optionally filtered by format."""
        ...
    
    # CRUD operations
    async def create_diagram(
        self, name: str, diagram: "DomainDiagram", format_type: str = "native"
    ) -> str: 
        """Create a new diagram with a unique ID."""
        ...
        
    async def get_diagram(self, diagram_id: str) -> "DomainDiagram | None": 
        """Get a diagram by its ID."""
        ...
        
    async def update_diagram(self, diagram_id: str, diagram: "DomainDiagram") -> None: 
        """Update an existing diagram."""
        ...
        
    async def delete_diagram(self, diagram_id: str) -> None: 
        """Delete a diagram from storage."""
        ...
    
    # Compilation
    def compile(self, domain_diagram: "DomainDiagram") -> "ExecutableDiagram":
        """Compile a DomainDiagram to ExecutableDiagram."""
        ...