"""Unified data structure interfaces for input resolution.

These interfaces provide consistent representations for edges, 
node outputs, and related data structures.
"""

from abc import ABC, abstractmethod
from typing import Any

from dipeo.diagram_generated import ContentType
# Note: ExecutableEdgeV2, NodeOutputProtocolV2, and StandardNodeOutput have been moved to
# dipeo.core.execution.executable_diagram for better architectural alignment
from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2


class EdgeMetadata:
    """Metadata associated with an edge."""
    
    def __init__(self, data: dict[str, Any] | None = None):
        self._data = data or {}
    
    @property
    def label(self) -> str | None:
        """Get edge label if present."""
        return self._data.get("label")
    
    @property
    def priority(self) -> int:
        """Get edge priority (default 0)."""
        return self._data.get("priority", 0)
    
    @property
    def condition(self) -> str | None:
        """Get edge condition if present."""
        return self._data.get("condition")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get arbitrary metadata value."""
        return self._data.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        return self._data[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self._data


class OutputExtractor(ABC):
    """Interface for extracting values from various output formats."""
    
    @abstractmethod
    def can_extract(self, output: Any) -> bool:
        """Check if this extractor can handle the output type."""
        pass
    
    @abstractmethod
    def extract(self, output: Any, key: str = "default") -> Any:
        """Extract value from output."""
        pass


class TransformationContext:
    """Context provided to transformation operations."""
    
    def __init__(
        self,
        edge: ExecutableEdgeV2,
        source_node_type: str,
        target_node_type: str,
        execution_count: int = 0
    ):
        self.edge = edge
        self.source_node_type = source_node_type
        self.target_node_type = target_node_type
        self.execution_count = execution_count
    
    @property
    def is_first_execution(self) -> bool:
        """Check if this is the first execution."""
        return self.execution_count <= 1
    
    @property
    def content_type(self) -> ContentType | None:
        """Get edge content type."""
        return self.edge.content_type