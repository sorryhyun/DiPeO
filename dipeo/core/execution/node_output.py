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
    
    value: T
    
    metadata: dict[str, Any]
    
    node_id: NodeID
    
    timestamp: datetime
    
    def get_output(self, key: str, default: Any = None) -> Any:
        ...
    
    def has_error(self) -> bool:
        ...
    
    def to_dict(self) -> dict[str, Any]:
        ...


@dataclass
class BaseNodeOutput(Generic[T], NodeOutputProtocol[T]):
    
    value: T
    node_id: NodeID
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    error: str | None = None
    
    def get_output(self, key: str, default: Any = None) -> Any:
        if hasattr(self.value, '__getitem__'):
            try:
                return self.value[key]
            except (KeyError, TypeError):
                pass
        
        return self.metadata.get(key, default)
    
    def has_error(self) -> bool:
        return self.error is not None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "node_id": self.node_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseNodeOutput:
        timestamp_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        
        return cls(
            value=data["value"],
            node_id=data["node_id"],
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
            error=data.get("error")
        )


@dataclass
class TextOutput(BaseNodeOutput[str]):
    
    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError(f"TextOutput value must be str, got {type(self.value)}")


@dataclass
class ConversationOutput(BaseNodeOutput[list['Message']]):
    
    def __post_init__(self):
        if not isinstance(self.value, list):
            raise TypeError(f"ConversationOutput value must be list, got {type(self.value)}")
    
    def get_last_message(self) -> 'Message' | None:
        return self.value[-1] if self.value else None
    
    def get_messages_by_role(self, role: str) -> list['Message']:
        return [msg for msg in self.value if hasattr(msg, 'role') and msg.role == role]


@dataclass
class ConditionOutput(BaseNodeOutput[bool]):
    
    true_output: Any = None  # Data for true branch
    false_output: Any = None  # Data for false branch
    
    def __post_init__(self):
        if not isinstance(self.value, bool):
            raise TypeError(f"ConditionOutput value must be bool, got {type(self.value)}")
        
        self.metadata.update({
            "condtrue": self.true_output,
            "condfalse": self.false_output,
            "active_branch": "condtrue" if self.value else "condfalse"
        })
    
    def get_branch_output(self) -> tuple[str, Any]:
        if self.value:
            return ("condtrue", self.true_output)
        else:
            return ("condfalse", self.false_output)
    
    def get_output(self, key: str, default: Any = None) -> Any:
        if key in ["condtrue", "condfalse", "active_branch"]:
            return self.metadata.get(key, default)
        return super().get_output(key, default)


@dataclass
class DataOutput(BaseNodeOutput[dict[str, Any]]):
    
    def __post_init__(self):
        if not isinstance(self.value, dict):
            raise TypeError(f"DataOutput value must be dict, got {type(self.value)}")
    
    def get_output(self, key: str, default: Any = None) -> Any:
        return self.value.get(key, default)


@dataclass
class ErrorOutput(BaseNodeOutput[str]):
    
    error_type: str = "ExecutionError"
    
    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError(f"ErrorOutput value must be str, got {type(self.value)}")
        
        self.error = self.value
        self.metadata.update({
            "error_type": self.error_type,
            "is_error": True
        })
    
    def has_error(self) -> bool:
        return True






def serialize_protocol(output: NodeOutputProtocol) -> dict[str, Any]:
    """Serialize protocol output for storage with type preservation."""
    base_dict = {
        "_protocol_type": output.__class__.__name__,
        "value": output.value,
        "metadata": output.metadata,
        "node_id": str(output.node_id)
    }
    
    if isinstance(output, ConditionOutput):
        base_dict["true_output"] = output.true_output
        base_dict["false_output"] = output.false_output
    elif isinstance(output, ErrorOutput):
        base_dict["error"] = output.error
        base_dict["error_type"] = output.error_type
    elif isinstance(output, DataOutput):
        pass
    elif isinstance(output, TextOutput):
        pass
    
    return base_dict


def deserialize_protocol(data: dict[str, Any]) -> NodeOutputProtocol:
    """Reconstruct protocol output from stored data with type information."""
    protocol_type = data.get("_protocol_type", "BaseNodeOutput")
    node_id = NodeID(data["node_id"])
    value = data["value"]
    metadata = data.get("metadata", {})
    
    if protocol_type == "ConditionOutput":
        return ConditionOutput(
            value=bool(value),
            node_id=node_id,
            metadata=metadata,
            true_output=data.get("true_output"),
            false_output=data.get("false_output")
        )
    elif protocol_type == "ErrorOutput":
        return ErrorOutput(
            value=str(value),
            node_id=node_id,
            metadata=metadata,
            error=data.get("error", str(value)),
            error_type=data.get("error_type", "UnknownError")
        )
    elif protocol_type == "TextOutput":
        return TextOutput(
            value=str(value),
            node_id=node_id,
            metadata=metadata
        )
    elif protocol_type == "DataOutput":
        return DataOutput(
            value=dict(value) if not isinstance(value, dict) else value,
            node_id=node_id,
            metadata=metadata
        )
    else:
        return BaseNodeOutput(
            value=value,
            node_id=node_id,
            metadata=metadata
        )