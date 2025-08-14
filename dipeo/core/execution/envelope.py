from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Any, TYPE_CHECKING, Protocol, TypeVar, runtime_checkable
from uuid import uuid4
import time
import io
import json
from datetime import datetime
from abc import abstractmethod

from dipeo.diagram_generated.enums import ContentType

if TYPE_CHECKING:
    import numpy as np
    from dipeo.diagram_generated import NodeID, TokenUsage, Status

T = TypeVar('T')


@runtime_checkable
class NodeOutputProtocol(Protocol[T]):
    """Protocol for node outputs in DiPeO execution system.
    
    This protocol defines the interface that all node outputs must implement.
    Both Envelope and legacy adapter classes implement this interface.
    """
    
    value: T
    metadata: str  # JSON string for intentional friction
    node_id: NodeID
    timestamp: datetime
    
    # Promoted typed fields
    token_usage: 'TokenUsage | None'
    execution_time: float | None
    retry_count: int
    status: 'Status | None'  # Node execution status
    
    def get_output(self, key: str, default: Any = None) -> Any:
        ...
    
    def has_error(self) -> bool:
        ...
    
    def to_dict(self) -> dict[str, Any]:
        ...
    
    def get_metadata_dict(self) -> dict[str, Any]:
        ...
    
    def set_metadata_dict(self, data: dict[str, Any]) -> None:
        ...
    
    def as_envelopes(self) -> list['Envelope']:
        """Convert to standardized envelopes"""
        ...
    
    def primary_envelope(self) -> 'Envelope':
        """Get primary output envelope"""
        ...

@dataclass(frozen=True)
class Envelope:
    """Immutable message envelope for inter-node communication.
    
    Now implements NodeOutputProtocol interface for seamless migration.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: str = field(default="")
    
    # Source
    produced_by: str = field(default="system")
    
    # Content
    content_type: ContentType = field(default="raw_text")
    schema_id: str | None = field(default=None)
    serialization_format: str | None = field(default=None)  # "numpy", "msgpack", "pickle", etc.
    body: Any = field(default=None)
    
    # Metadata
    meta: dict[str, Any] = field(default_factory=dict)
    
    def with_meta(self, **kwargs) -> Envelope:
        """Create new envelope with updated metadata"""
        new_meta = {**self.meta, **kwargs}
        return replace(self, meta=new_meta)
    
    def with_iteration(self, iteration: int) -> Envelope:
        """Tag with iteration number"""
        return self.with_meta(iteration=iteration)
    
    def with_branch(self, branch_id: str) -> Envelope:
        """Tag with branch identifier"""
        return self.with_meta(branch_id=branch_id)
    
    # NodeOutputProtocol compatibility methods
    @property
    def value(self) -> Any:
        """Get the envelope body for NodeOutputProtocol compatibility."""
        return self.body
    
    @property
    def node_id(self) -> 'NodeID':
        """Get node ID for NodeOutputProtocol compatibility."""
        from dipeo.diagram_generated import NodeID
        return NodeID(self.produced_by)
    
    @property
    def metadata(self) -> str:
        """Get metadata as JSON string for NodeOutputProtocol compatibility."""
        return json.dumps(self.meta) if self.meta else "{}"
    
    @property
    def timestamp(self) -> datetime:
        """Get timestamp for NodeOutputProtocol compatibility."""
        if "timestamp" in self.meta and isinstance(self.meta["timestamp"], (int, float)):
            return datetime.fromtimestamp(self.meta["timestamp"])
        return datetime.now()
    
    @property
    def token_usage(self) -> 'TokenUsage | None':
        """Get token usage for NodeOutputProtocol compatibility."""
        if "token_usage" in self.meta and self.meta["token_usage"]:
            from dipeo.diagram_generated import TokenUsage
            usage_data = self.meta["token_usage"]
            if isinstance(usage_data, dict):
                return TokenUsage(
                    input=usage_data.get("input", 0),
                    output=usage_data.get("output", 0),
                    cached=usage_data.get("cached"),
                    total=usage_data.get("total")
                )
        return None
    
    @property
    def execution_time(self) -> float | None:
        """Get execution time for NodeOutputProtocol compatibility."""
        return self.meta.get("execution_time")
    
    @property
    def retry_count(self) -> int:
        """Get retry count for NodeOutputProtocol compatibility."""
        return self.meta.get("retry_count", 0)
    
    @property
    def status(self) -> 'Status | None':
        """Get status for NodeOutputProtocol compatibility."""
        if "status" in self.meta:
            from dipeo.diagram_generated import Status
            status_val = self.meta["status"]
            if isinstance(status_val, str):
                try:
                    return Status(status_val)
                except ValueError:
                    pass
        return None
    
    @property
    def error(self) -> str | None:
        """Get error message if present."""
        return self.meta.get("error")
    
    def get_output(self, key: str, default: Any = None) -> Any:
        """Get output value by key for NodeOutputProtocol compatibility."""
        # First check body if it's a dict
        if isinstance(self.body, dict):
            if key in self.body:
                return self.body[key]
        
        # Then check metadata
        return self.meta.get(key, default)
    
    def has_error(self) -> bool:
        """Check if envelope represents an error."""
        return "error" in self.meta and self.meta["error"] is not None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for NodeOutputProtocol compatibility."""
        result = {
            "value": self.body,
            "node_id": self.produced_by,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "error": self.error,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "status": self.status.value if self.status else None
        }
        
        # Include token_usage if present
        token_usage = self.token_usage
        if token_usage:
            result["token_usage"] = {
                "input": token_usage.input,
                "output": token_usage.output,
                "cached": token_usage.cached,
                "total": token_usage.total
            }
        else:
            result["token_usage"] = None
        
        return result
    
    def get_metadata_dict(self) -> dict[str, Any]:
        """Get metadata as dictionary for NodeOutputProtocol compatibility."""
        return dict(self.meta)
    
    def set_metadata_dict(self, data: dict[str, Any]) -> None:
        """NodeOutputProtocol compatibility - but Envelope is immutable."""
        raise NotImplementedError("Envelope is immutable. Use with_meta() to create new envelope with updated metadata.")
    
    def as_envelopes(self) -> list['Envelope']:
        """Return self as list for NodeOutputProtocol compatibility."""
        return [self]
    
    def primary_envelope(self) -> 'Envelope':
        """Return self for NodeOutputProtocol compatibility."""
        return self

class EnvelopeFactory:
    """Factory for creating envelopes with backward compatibility support"""
    
    @staticmethod
    def text(content: str, node_id: str | None = None, **kwargs) -> Envelope:
        """Create text envelope with optional node_id for compatibility"""
        meta = kwargs.pop("meta", {})
        meta["timestamp"] = meta.get("timestamp", time.time())
        
        # Support node_id parameter for backward compatibility
        if node_id:
            kwargs.setdefault("produced_by", node_id)
        
        return Envelope(
            content_type=ContentType.RAW_TEXT,
            body=content,
            meta=meta,
            **kwargs
        )
    
    @staticmethod
    def json(data: Any, schema_id: str | None = None, node_id: str | None = None, **kwargs) -> Envelope:
        """Create JSON envelope with optional node_id for compatibility"""
        meta = kwargs.pop("meta", {})
        meta["timestamp"] = meta.get("timestamp", time.time())
        
        # Support node_id parameter for backward compatibility
        if node_id:
            kwargs.setdefault("produced_by", node_id)
        
        return Envelope(
            content_type=ContentType.OBJECT,
            schema_id=schema_id,
            body=data,
            meta=meta,
            **kwargs
        )
    
    @staticmethod
    def conversation(state: dict, node_id: str | None = None, **kwargs) -> Envelope:
        """Create conversation envelope with optional node_id for compatibility"""
        meta = kwargs.pop("meta", {})
        meta["timestamp"] = meta.get("timestamp", time.time())
        
        # Support node_id parameter for backward compatibility
        if node_id:
            kwargs.setdefault("produced_by", node_id)
        
        return Envelope(
            content_type=ContentType.CONVERSATION_STATE,
            body=state,
            meta=meta,
            **kwargs
        )
    
    @staticmethod
    def numpy_array(array: "np.ndarray", **kwargs) -> Envelope:
        """Create envelope for numpy array with safe serialization"""
        import numpy as np
        
        # Use numpy's safe format instead of pickle
        buffer = io.BytesIO()
        np.save(buffer, array, allow_pickle=False)
        
        return Envelope(
            content_type=ContentType.BINARY,
            serialization_format="numpy",
            body=buffer.getvalue(),
            meta={
                "timestamp": time.time(),
                "dtype": str(array.dtype),
                "shape": array.shape,
                "size": array.size
            },
            **kwargs
        )
    
    @staticmethod
    def binary(data: bytes, format: str = "raw", **kwargs) -> Envelope:
        """Create envelope for generic binary data"""
        meta = kwargs.pop("meta", {})
        meta["timestamp"] = meta.get("timestamp", time.time())
        
        return Envelope(
            content_type=ContentType.BINARY,
            serialization_format=format,
            body=data,
            meta=meta,
            **kwargs
        )
    
    @staticmethod
    def error(error_msg: str, error_type: str = "ExecutionError", node_id: str | None = None, **kwargs) -> Envelope:
        """Create error envelope for backward compatibility"""
        meta = kwargs.pop("meta", {})
        meta["timestamp"] = meta.get("timestamp", time.time())
        meta["error"] = error_msg
        meta["error_type"] = error_type
        meta["is_error"] = True
        
        # Support node_id parameter for backward compatibility
        if node_id:
            kwargs.setdefault("produced_by", node_id)
        
        return Envelope(
            content_type=ContentType.RAW_TEXT,
            body=error_msg,
            meta=meta,
            **kwargs
        )
    
    @staticmethod
    def create(content_type: ContentType, body: Any, node_id: str | None = None, **kwargs) -> Envelope:
        """Generic factory method for creating envelopes"""
        meta = kwargs.pop("meta", {})
        meta["timestamp"] = meta.get("timestamp", time.time())
        
        # Support node_id parameter for backward compatibility
        if node_id:
            kwargs.setdefault("produced_by", node_id)
        
        return Envelope(
            content_type=content_type,
            body=body,
            meta=meta,
            **kwargs
        )


def serialize_protocol(output: NodeOutputProtocol) -> dict[str, Any]:
    """Serialize protocol output for storage.
    
    Always produces consistent Envelope format for new data.
    """
    # Always serialize as Envelope format for consistency
    if isinstance(output, Envelope):
        # Direct serialization for Envelope instances
        return {
            "envelope_format": True,  # Discriminator for deserialization
            "id": output.id,
            "trace_id": output.trace_id,
            "produced_by": output.produced_by,
            "content_type": output.content_type.value if hasattr(output.content_type, 'value') else output.content_type,
            "schema_id": output.schema_id,
            "serialization_format": output.serialization_format,
            "body": output.body,
            "meta": output.meta
        }
    
    # Convert any other NodeOutputProtocol to Envelope format
    # This ensures consistent storage format
    meta = {}
    
    # Parse metadata if it's a JSON string
    if hasattr(output, 'metadata') and output.metadata:
        try:
            if isinstance(output.metadata, str):
                meta = json.loads(output.metadata)
            elif isinstance(output.metadata, dict):
                meta = output.metadata
        except json.JSONDecodeError:
            pass
    
    # Add structured fields to metadata
    if hasattr(output, 'execution_time') and output.execution_time is not None:
        meta['execution_time'] = output.execution_time
    if hasattr(output, 'retry_count') and output.retry_count:
        meta['retry_count'] = output.retry_count
    if hasattr(output, 'timestamp'):
        meta['timestamp'] = output.timestamp.timestamp() if hasattr(output.timestamp, 'timestamp') else time.time()
    
    # Add token usage if present
    if hasattr(output, 'token_usage') and output.token_usage:
        meta['token_usage'] = {
            "input": output.token_usage.input,
            "output": output.token_usage.output,
            "cached": output.token_usage.cached,
            "total": output.token_usage.total
        }
    
    # Add status if present
    if hasattr(output, 'status') and output.status:
        meta['status'] = output.status.value if hasattr(output.status, 'value') else str(output.status)
    
    # Determine content type based on value
    value = output.value if hasattr(output, 'value') else None
    if isinstance(value, dict):
        content_type = ContentType.OBJECT
    else:
        content_type = ContentType.RAW_TEXT
    
    # Return in Envelope format
    return {
        "envelope_format": True,
        "id": str(uuid4()),
        "trace_id": "",
        "produced_by": str(output.node_id) if hasattr(output, 'node_id') else "system",
        "content_type": content_type.value if hasattr(content_type, 'value') else content_type,
        "schema_id": None,
        "serialization_format": None,
        "body": value,
        "meta": meta
    }


def deserialize_protocol(data: dict[str, Any]) -> NodeOutputProtocol:
    """Reconstruct protocol output from stored data.
    
    Handles both new Envelope format and legacy NodeOutput format for backward compatibility.
    """
    from dipeo.diagram_generated import TokenUsage, NodeID, Status
    
    # Check for new Envelope format (using discriminator)
    if data.get("envelope_format") or data.get("_envelope_format"):
        # New Envelope format
        content_type_val = data.get("content_type", "raw_text")
        
        # Handle content_type conversion
        if isinstance(content_type_val, str):
            try:
                # Try to convert to ContentType enum
                content_type = ContentType(content_type_val)
            except (ValueError, KeyError):
                # If not a valid enum value, default to RAW_TEXT
                content_type = ContentType.RAW_TEXT
        else:
            content_type = content_type_val
        
        return Envelope(
            id=data.get("id", str(uuid4())),
            trace_id=data.get("trace_id", ""),
            produced_by=data.get("produced_by", "system"),
            content_type=content_type,
            schema_id=data.get("schema_id"),
            serialization_format=data.get("serialization_format"),
            body=data.get("body"),
            meta=data.get("meta", {})
        )
    
    # Legacy NodeOutput format - convert to Envelope
    # This path maintains backward compatibility with existing stored data
    node_id = data.get("node_id", "unknown")
    value = data.get("value")
    metadata_str = data.get("metadata", "{}")
    
    # Parse metadata if it's a JSON string
    meta = {}
    if isinstance(metadata_str, str):
        try:
            meta = json.loads(metadata_str)
        except (json.JSONDecodeError, TypeError):
            meta = {}
    elif isinstance(metadata_str, dict):
        meta = metadata_str
    
    # Determine content type based on legacy protocol type or value type
    protocol_type = data.get("_protocol_type", data.get("_type", ""))
    
    # Map legacy types to ContentType
    if "Condition" in protocol_type:
        content_type = ContentType.RAW_TEXT  # Store condition result as text
        # Add condition-specific metadata
        meta["condition_result"] = value
        meta["condtrue"] = data.get("true_output")
        meta["condfalse"] = data.get("false_output")
        meta["active_branch"] = "condtrue" if value else "condfalse"
    elif "Conversation" in protocol_type:
        content_type = ContentType.CONVERSATION_STATE
    elif "Data" in protocol_type or isinstance(value, dict):
        content_type = ContentType.OBJECT
    else:
        content_type = ContentType.RAW_TEXT
    
    # Migrate legacy fields to metadata
    if data.get("token_usage"):
        meta["token_usage"] = data["token_usage"]
    if data.get("execution_time") is not None:
        meta["execution_time"] = data["execution_time"]
    if data.get("retry_count"):
        meta["retry_count"] = data["retry_count"]
    if data.get("status"):
        meta["status"] = data["status"]
    if data.get("error"):
        meta["error"] = data["error"]
    if data.get("timestamp"):
        # Handle timestamp conversion
        ts = data["timestamp"]
        if isinstance(ts, str):
            try:
                # Parse ISO format timestamp
                from datetime import datetime
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                meta["timestamp"] = dt.timestamp()
            except:
                meta["timestamp"] = time.time()
        else:
            meta["timestamp"] = ts
    
    # Create Envelope with migrated data
    return Envelope(
        id=str(uuid4()),
        trace_id="",
        produced_by=str(node_id),
        content_type=content_type,
        schema_id=None,
        serialization_format=None,
        body=value,
        meta=meta
    )
    
