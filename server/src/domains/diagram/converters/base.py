"""Base converter interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List, Optional
from ..models.domain import DomainDiagram


class DiagramConverter(ABC):
    """Abstract base class for diagram converters."""
    
    @abstractmethod
    def serialize(self, diagram: DomainDiagram) -> str:
        """Convert domain diagram to format-specific string."""
        pass
    
    @abstractmethod
    def deserialize(self, content: str) -> DomainDiagram:
        """Convert format-specific string to domain diagram."""
        pass
    
    def validate(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate content without full deserialization.
        Returns (is_valid, list_of_errors)
        """
        try:
            self.deserialize(content)
            return True, []
        except Exception as e:
            return False, [str(e)]
    
    def detect_format_confidence(self, content: str) -> float:
        """
        Return confidence score (0.0-1.0) that content matches this format.
        Used for automatic format detection.
        """
        try:
            self.deserialize(content)
            return 1.0
        except:
            return 0.0