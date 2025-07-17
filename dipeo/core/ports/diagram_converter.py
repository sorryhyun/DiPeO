"""Diagram converter port definitions."""

from abc import ABC, abstractmethod
from typing import Any


class DiagramConverter(ABC):
    """Abstract base class for diagram converters."""
    
    @abstractmethod
    def serialize(self, diagram: dict[str, Any]) -> str:
        """Serialize diagram to string format."""
        pass

    @abstractmethod
    def deserialize(self, content: str) -> dict[str, Any]:
        """Deserialize string content to diagram."""
        pass

    def validate(self, content: str) -> tuple[bool, list[str]]:
        """Validate diagram content."""
        try:
            self.deserialize(content)
            return True, []
        except Exception as e:
            return False, [str(e)]

    def detect_format_confidence(self, content: str) -> float:
        """Detect confidence that content matches this format."""
        try:
            self.deserialize(content)
            return 1.0
        except Exception:
            return 0.0


class FormatStrategy(ABC):
    """Abstract base class for format conversion strategies."""
    
    @abstractmethod
    def parse(self, content: str) -> dict[str, Any]:
        """Parse content into diagram data."""
        pass

    @abstractmethod
    def format(self, data: dict[str, Any]) -> str:
        """Format diagram data into string."""
        pass

    @abstractmethod
    def extract_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract nodes from diagram data."""
        pass

    @abstractmethod
    def extract_arrows(
        self, data: dict[str, Any], nodes: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract arrows from diagram data."""
        pass

    @abstractmethod
    def build_export_data(self, diagram: dict[str, Any]) -> dict[str, Any]:
        """Build data for export."""
        pass

    @abstractmethod
    def deserialize_to_domain(self, content: str) -> Any:
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
    def serialize_from_domain(self, diagram: Any) -> str:
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