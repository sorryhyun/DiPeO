"""Type-safe NodeOutput protocol hierarchy for DiPeO execution system.

This module provides a protocol-based approach to node outputs with strong typing,
clear contracts, and specialized output types for different node categories.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:
    from dipeo.models import Message, NodeID

T = TypeVar('T')


@runtime_checkable
class NodeOutputProtocol(Protocol[T]):
    """Protocol for type-safe node outputs."""
    
    @property
    @abstractmethod
    def value(self) -> T:
        """The primary output value with specific type."""
        ...
    
    @property
    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """Additional metadata (execution info, tokens, etc)."""
        ...
    
    @property
    @abstractmethod
    def node_id(self) -> NodeID:
        """The node that produced this output."""
        ...
    
    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """When this output was generated."""
        ...
    
    @abstractmethod
    def get_output(self, key: str, default: Any = None) -> Any:
        """Get a specific output by key (for multi-output nodes)."""
        ...
    
    @abstractmethod
    def has_error(self) -> bool:
        """Check if this output represents an error state."""
        ...
    
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for storage."""
        ...


# Base implementation
@dataclass
class BaseNodeOutput(Generic[T]):
    """Base implementation of NodeOutput with common functionality."""
    
    value: T
    node_id: NodeID
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    error: str | None = None
    
    def get_output(self, key: str, default: Any = None) -> Any:
        """Get output by key from metadata or value."""
        if hasattr(self.value, '__getitem__'):
            try:
                return self.value[key]
            except (KeyError, TypeError):
                pass
        
        return self.metadata.get(key, default)
    
    def has_error(self) -> bool:
        """Check if this output has an error."""
        return self.error is not None
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "value": self.value,
            "node_id": self.node_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseNodeOutput:
        """Deserialize from dictionary."""
        timestamp_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        
        return cls(
            value=data["value"],
            node_id=data["node_id"],
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
            error=data.get("error")
        )


# Specialized output types
@dataclass
class TextOutput(BaseNodeOutput[str]):
    """Output for text-generating nodes (like PersonJob)."""
    
    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError(f"TextOutput value must be str, got {type(self.value)}")


@dataclass
class ConversationOutput(BaseNodeOutput[list['Message']]):
    """Output for conversation-based nodes."""
    
    def __post_init__(self):
        if not isinstance(self.value, list):
            raise TypeError(f"ConversationOutput value must be list, got {type(self.value)}")
    
    def get_last_message(self) -> 'Message' | None:
        """Get the most recent message."""
        return self.value[-1] if self.value else None
    
    def get_messages_by_role(self, role: str) -> list['Message']:
        """Get all messages from a specific role."""
        return [msg for msg in self.value if hasattr(msg, 'role') and msg.role == role]


@dataclass
class ConditionOutput(BaseNodeOutput[bool]):
    """Output for condition nodes with structured branch data."""
    
    true_output: Any = None  # Data for true branch
    false_output: Any = None  # Data for false branch
    
    def __post_init__(self):
        if not isinstance(self.value, bool):
            raise TypeError(f"ConditionOutput value must be bool, got {type(self.value)}")
        
        # Store branch outputs in metadata for consistency
        self.metadata.update({
            "condtrue": self.true_output,
            "condfalse": self.false_output,
            "active_branch": "condtrue" if self.value else "condfalse"
        })
    
    def get_branch_output(self) -> tuple[str, Any]:
        """Get the active branch name and its data."""
        if self.value:
            return ("condtrue", self.true_output)
        else:
            return ("condfalse", self.false_output)
    
    def get_output(self, key: str, default: Any = None) -> Any:
        """Override to handle condition-specific keys."""
        if key in ["condtrue", "condfalse", "active_branch"]:
            return self.metadata.get(key, default)
        return super().get_output(key, default)


@dataclass
class DataOutput(BaseNodeOutput[dict[str, Any]]):
    """Output for nodes that produce structured data."""
    
    def __post_init__(self):
        if not isinstance(self.value, dict):
            raise TypeError(f"DataOutput value must be dict, got {type(self.value)}")
    
    def get_output(self, key: str, default: Any = None) -> Any:
        """Get value from the data dictionary."""
        return self.value.get(key, default)


@dataclass
class ErrorOutput(BaseNodeOutput[str]):
    """Output for nodes that encountered errors."""
    
    error_type: str = "ExecutionError"
    
    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError(f"ErrorOutput value must be str, got {type(self.value)}")
        
        # Always set error field
        self.error = self.value
        self.metadata.update({
            "error_type": self.error_type,
            "is_error": True
        })
    
    def has_error(self) -> bool:
        """Error outputs always have errors."""
        return True


# Compatibility layer
class OutputCompatibilityWrapper:
    """Wraps new outputs to look like old ones during migration."""
    
    def __init__(self, new_output: NodeOutputProtocol):
        self._new_output = new_output
    
    @property
    def value(self) -> Any:
        """Legacy value access."""
        return self._new_output.value
    
    @property
    def metadata(self) -> dict[str, Any]:
        """Legacy metadata access."""
        return self._new_output.metadata
    
    def get(self, key: str, default: Any = None) -> Any:
        """Legacy dict-style access."""
        return self._new_output.get_output(key, default)


class LegacyNodeOutput:
    """Legacy output class for backward compatibility."""
    
    def __init__(self, value: Any, metadata: dict[str, Any] | None = None):
        self.value = value
        self.metadata = metadata or {}
    
    def to_modern(self, node_id: NodeID) -> NodeOutputProtocol:
        """Convert to modern output format."""
        # Determine appropriate output type based on value
        if isinstance(self.value, str):
            return TextOutput(value=self.value, node_id=node_id, metadata=self.metadata)
        elif isinstance(self.value, bool):
            return ConditionOutput(
                value=self.value,
                node_id=node_id,
                metadata=self.metadata,
                true_output=self.metadata.get("condtrue"),
                false_output=self.metadata.get("condfalse")
            )
        elif isinstance(self.value, dict):
            return DataOutput(value=self.value, node_id=node_id, metadata=self.metadata)
        else:
            # Generic fallback
            return BaseNodeOutput(value=self.value, node_id=node_id, metadata=self.metadata)