from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Any, TYPE_CHECKING, TypeVar
from uuid import uuid4
import time
import io
import json

from dipeo.diagram_generated.enums import ContentType

if TYPE_CHECKING:
    import numpy as np

T = TypeVar('T')


@dataclass(frozen=True)
class Envelope:
    """Immutable message envelope for inter-node communication."""
    
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
    
    @property
    def error(self) -> str | None:
        """Get error message if present."""
        return self.meta.get("error")
    
    def has_error(self) -> bool:
        """Check if envelope represents an error."""
        return "error" in self.meta and self.meta["error"] is not None

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
        np.save(buffer, array, allow_pickle=False)  # type: ignore[arg-type]
        
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


def serialize_protocol(output: Envelope) -> dict[str, Any]:
    """Serialize envelope for storage.
    
    Always produces consistent Envelope format.
    """
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


def deserialize_protocol(data: dict[str, Any]) -> Envelope:
    """Reconstruct envelope from stored data.
    
    Handles both new Envelope format and legacy NodeOutput format for backward compatibility.
    """
    
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
    
