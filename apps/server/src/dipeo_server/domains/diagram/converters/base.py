"""Base converter interface and format strategy abstract base class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from dipeo_domain import DomainDiagram


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
        """Validate content without full deserialization."""
        try:
            self.deserialize(content)
            return True, []
        except Exception as e:
            return False, [str(e)]

    def detect_format_confidence(self, content: str) -> float:
        """Return format confidence score (0.0-1.0)."""
        try:
            self.deserialize(content)
            return 1.0
        except Exception:
            return 0.0


class FormatStrategy(ABC):
    """Abstract base class for format conversion strategies."""

    @abstractmethod
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse content to intermediate format."""
        pass

    @abstractmethod
    def format(self, data: Dict[str, Any]) -> str:
        """Format intermediate data to string."""
        pass

    @abstractmethod
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract nodes from parsed data."""
        pass

    @abstractmethod
    def extract_arrows(
        self, data: Dict[str, Any], nodes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract arrows from parsed data."""
        pass

    @abstractmethod
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        """Build export data from domain diagram."""
        pass

    @abstractmethod
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence that data matches this format."""
        pass

    @property
    @abstractmethod
    def format_id(self) -> str:
        """Unique identifier for this format."""
        pass

    @property
    @abstractmethod
    def format_info(self) -> Dict[str, str]:
        """Metadata about this format."""
        pass

    def quick_match(self, content: str) -> bool:
        """Quick heuristic to check if content might match this format.
        
        Default implementation tries to parse.
        Override for faster format detection.
        """
        try:
            self.parse(content)
            return True
        except Exception:
            return False
