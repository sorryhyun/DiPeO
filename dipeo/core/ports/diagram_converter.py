"""Diagram storage serialization port definitions.

This module defines interfaces for serializing DomainDiagram models to/from
string formats (JSON, YAML) for file storage purposes only.

Note: GraphQL and internal APIs should use DomainDiagram directly without serialization.
"""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from dipeo.diagram_generated import DomainDiagram


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
            

# Keep old name for backward compatibility but mark as deprecated
class DiagramConverter(DiagramStorageSerializer):
    """DEPRECATED: Use DiagramStorageSerializer instead.
    
    This class exists only for backward compatibility.
    """
    
    def serialize(self, diagram: "DomainDiagram") -> str:
        """DEPRECATED: Use serialize_for_storage() instead."""
        return self.serialize_for_storage(diagram, format="native")
    
    def deserialize(self, content: str) -> "DomainDiagram":
        """DEPRECATED: Use deserialize_from_storage() instead."""
        return self.deserialize_from_storage(content)


class FormatStrategy(ABC):
    
    @abstractmethod
    def parse(self, content: str) -> Any:
        """Parse content to intermediate format (dict, Pydantic model, etc).
        
        The return type is Any to allow format-specific representations.
        This is only used internally by the strategy for processing.
        """
        pass

    @abstractmethod
    def format(self, data: Any) -> str:
        """Format data to string representation.
        
        The data type is Any to allow format-specific representations.
        This is only used internally by the strategy for serialization.
        """
        pass

    @abstractmethod
    def deserialize_to_domain(self, content: str) -> "DomainDiagram":
        """Deserialize format-specific string to domain diagram.
        
        This method should handle the complete conversion from the format-specific
        string representation to a DomainDiagram object, including:
        - Parsing the content
        - Creating domain nodes with proper types
        - Creating domain arrows with content types
        - Creating/generating handles
        - Handling format-specific transformations
        """
        pass

    @abstractmethod
    def serialize_from_domain(self, diagram: "DomainDiagram") -> str:
        """Serialize domain diagram to format-specific string.
        
        This method should handle the complete conversion from a DomainDiagram
        object to the format-specific string representation.
        """
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