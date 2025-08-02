"""Unified data structure interfaces for input resolution.

These interfaces provide consistent representations for edges, 
node outputs, and related data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol

from dipeo.diagram_generated import ContentType, NodeID


@dataclass(frozen=True)
class ExecutableEdgeV2:
    """Enhanced edge representation with all resolution rules.
    
    This unified structure contains all information needed for both
    compile-time validation and runtime execution.
    """
    # Identity
    id: str
    source_node_id: NodeID
    target_node_id: NodeID
    
    # Connection details
    source_output: str = "default"
    target_input: str = "default"
    
    # Transformation rules (determined at compile time)
    content_type: ContentType | None = None
    transform_rules: dict[str, Any] = field(default_factory=dict)
    
    # Runtime behavior hints
    is_conditional: bool = False
    requires_first_execution: bool = False
    
    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def get_transform_rule(self, rule_type: str) -> Any | None:
        """Get a specific transformation rule."""
        return self.transform_rules.get(rule_type)
    
    def has_transform_rule(self, rule_type: str) -> bool:
        """Check if a transformation rule exists."""
        return rule_type in self.transform_rules


class NodeOutputProtocolV2(Protocol):
    """Enhanced protocol for node outputs with consistent access patterns."""
    
    @property
    def value(self) -> Any:
        """Primary output value."""
        ...
    
    @property
    def outputs(self) -> dict[str, Any]:
        """Named outputs dictionary."""
        ...
    
    @property
    def metadata(self) -> dict[str, Any]:
        """Output metadata."""
        ...
    
    def get_output(self, name: str = "default") -> Any:
        """Get a specific named output or default value."""
        ...
    
    def has_output(self, name: str) -> bool:
        """Check if a named output exists."""
        ...


@dataclass
class StandardNodeOutput:
    """Standard implementation of NodeOutputProtocolV2."""
    
    value: Any
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def get_output(self, name: str = "default") -> Any:
        """Get a specific named output or default value."""
        if name == "default":
            return self.outputs.get(name, self.value)
        return self.outputs.get(name)
    
    def has_output(self, name: str) -> bool:
        """Check if a named output exists."""
        if name == "default":
            return True  # Always has default
        return name in self.outputs
    
    @classmethod
    def from_value(cls, value: Any) -> "StandardNodeOutput":
        """Create from a simple value."""
        return cls(value=value, outputs={"default": value})
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StandardNodeOutput":
        """Create from a dictionary representation."""
        if "value" in data:
            return cls(
                value=data["value"],
                outputs=data.get("outputs", {"default": data["value"]}),
                metadata=data.get("metadata", {})
            )
        else:
            # Treat entire dict as outputs
            return cls(
                value=data.get("default", data),
                outputs=data,
                metadata={}
            )


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