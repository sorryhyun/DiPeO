from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Any, TYPE_CHECKING, TypeVar
from uuid import uuid4
import time
import io
import json
import logging
import warnings
import os
from collections import defaultdict

from dipeo.diagram_generated.enums import ContentType

if TYPE_CHECKING:
    import numpy as np

T = TypeVar('T')

# Counters for tracking fallback conversions
_fallback_counters = defaultdict(int)
logger = logging.getLogger(__name__)


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
    
    def as_text(self) -> str:
        """Extract text content - strict version."""
        if self.content_type == ContentType.RAW_TEXT:
            return str(self.body) if self.body is not None else ""
        else:
            raise ValueError(f"Cannot convert {self.content_type} to text - use to_text() for strict checking")
    
    def as_json(self, model: type[T] | None = None) -> T | dict | list:
        """Extract and optionally validate JSON content - strict version."""
        if self.content_type != ContentType.OBJECT:
            raise ValueError(f"Cannot extract JSON from {self.content_type} - use to_json() for strict checking")
        
        data = self.body
        
        # Validate with Pydantic if model provided
        if model:
            try:
                from pydantic import BaseModel, ValidationError
                if issubclass(model, BaseModel):
                    return model.model_validate(data)
            except (ImportError, ValidationError) as e:
                raise ValueError(f"Schema validation failed: {e}")
        
        return data
    
    def as_bytes(self) -> bytes:
        """Extract binary content - strict version."""
        if self.content_type == ContentType.BINARY:
            if isinstance(self.body, bytes):
                return self.body
            else:
                raise ValueError(f"Binary envelope contains non-bytes data: {type(self.body)}")
        else:
            raise ValueError(f"Cannot extract binary from {self.content_type} - use to_bytes() for strict checking")
    
    def as_conversation(self) -> dict:
        """Extract conversation state."""
        if self.content_type != ContentType.CONVERSATION_STATE:
            raise ValueError(f"Expected conversation_state, got {self.content_type}")
        return self.body
    
    # Strict conversion methods (no implicit conversions)
    def to_text(self) -> str:
        """Extract text content - strict version without fallbacks.
        
        Raises:
            TypeError: If envelope is not RAW_TEXT content type
        """
        if self.content_type is not ContentType.RAW_TEXT:
            raise TypeError(f"Envelope is not RAW_TEXT, got {self.content_type}")
        if not isinstance(self.body, str):
            raise TypeError(f"RAW_TEXT body must be str, got {type(self.body)}")
        return self.body
    
    def to_json(self) -> Any:
        """Extract JSON content - strict version without fallbacks.
        
        Raises:
            TypeError: If envelope is not OBJECT content type
        """
        if self.content_type is not ContentType.OBJECT:
            raise TypeError(f"Envelope is not OBJECT (JSON), got {self.content_type}")
        # Validate JSON-serializable
        if self.body is not None:
            try:
                json.dumps(self.body)
            except (TypeError, ValueError) as e:
                raise TypeError(f"OBJECT body must be JSON-serializable: {e}")
        return self.body
    
    def to_bytes(self) -> bytes:
        """Extract binary content - strict version without fallbacks.
        
        Raises:
            TypeError: If envelope is not BINARY content type
        """
        if self.content_type is not ContentType.BINARY:
            raise TypeError(f"Envelope is not BINARY, got {self.content_type}")
        if not isinstance(self.body, (bytes, bytearray, memoryview)):
            raise TypeError(f"BINARY body must be bytes-like, got {type(self.body)}")
        return bytes(self.body)

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


class StrictEnvelopeFactory:
    """Strict envelope factory with no implicit conversions or fallbacks.
    
    This factory enforces:
    - Explicit content type matching
    - Type validation at creation time
    - Required metadata fields
    - No auto-coercion between types
    """
    
    @staticmethod
    def _make_meta(
        meta: dict[str, Any] | None, 
        produced_by: str | None, 
        trace_id: str | None
    ) -> dict[str, Any]:
        """Create metadata with required fields."""
        result = meta.copy() if meta else {}
        result["timestamp"] = result.get("timestamp", time.time())
        if produced_by:
            result["produced_by"] = produced_by
        if trace_id:
            result["trace_id"] = trace_id
        return result
    
    @staticmethod
    def text(
        content: str, 
        *, 
        produced_by: str | None = None, 
        trace_id: str | None = None, 
        meta: dict[str, Any] | None = None
    ) -> Envelope:
        """Create a text envelope with strict validation.
        
        Args:
            content: The text content (must be str)
            produced_by: Node or component that produced this envelope
            trace_id: Execution trace ID
            meta: Additional metadata
            
        Raises:
            TypeError: If content is not a string
        """
        if not isinstance(content, str):
            raise TypeError(f"text() requires str content, got {type(content)}")
        
        return Envelope(
            content_type=ContentType.RAW_TEXT,
            body=content,
            produced_by=produced_by or "system",
            trace_id=trace_id or "",
            meta=StrictEnvelopeFactory._make_meta(meta, produced_by, trace_id)
        )
    
    @staticmethod
    def json(
        value: Any,
        *,
        produced_by: str | None = None,
        trace_id: str | None = None,
        meta: dict[str, Any] | None = None,
        schema_id: str | None = None
    ) -> Envelope:
        """Create a JSON envelope with strict validation.
        
        Args:
            value: JSON-serializable value
            produced_by: Node or component that produced this envelope
            trace_id: Execution trace ID
            meta: Additional metadata
            schema_id: Optional schema identifier
            
        Raises:
            TypeError: If value is not JSON-serializable
        """
        # Validate JSON-serializability eagerly
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            raise TypeError(f"json() requires JSON-serializable value: {e}")
        
        return Envelope(
            content_type=ContentType.OBJECT,
            body=value,
            schema_id=schema_id,
            produced_by=produced_by or "system",
            trace_id=trace_id or "",
            meta=StrictEnvelopeFactory._make_meta(meta, produced_by, trace_id)
        )
    
    @staticmethod
    def binary(
        data: bytes | bytearray | memoryview,
        *,
        produced_by: str | None = None,
        trace_id: str | None = None,
        meta: dict[str, Any] | None = None,
        format: str = "raw"
    ) -> Envelope:
        """Create a binary envelope with strict validation.
        
        Args:
            data: Binary data (must be bytes-like)
            produced_by: Node or component that produced this envelope
            trace_id: Execution trace ID
            meta: Additional metadata
            format: Binary format identifier
            
        Raises:
            TypeError: If data is not bytes-like
        """
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError(f"binary() requires bytes-like data, got {type(data)}")
        
        return Envelope(
            content_type=ContentType.BINARY,
            body=bytes(data),  # Convert to bytes for consistency
            serialization_format=format,
            produced_by=produced_by or "system",
            trace_id=trace_id or "",
            meta=StrictEnvelopeFactory._make_meta(meta, produced_by, trace_id)
        )
    
    @staticmethod
    def conversation(
        state: dict,
        *,
        produced_by: str | None = None,
        trace_id: str | None = None,
        meta: dict[str, Any] | None = None
    ) -> Envelope:
        """Create a conversation envelope with strict validation.
        
        Args:
            state: Conversation state dictionary
            produced_by: Node or component that produced this envelope
            trace_id: Execution trace ID
            meta: Additional metadata
            
        Raises:
            TypeError: If state is not a dictionary
        """
        if not isinstance(state, dict):
            raise TypeError(f"conversation() requires dict state, got {type(state)}")
        
        return Envelope(
            content_type=ContentType.CONVERSATION_STATE,
            body=state,
            produced_by=produced_by or "system",
            trace_id=trace_id or "",
            meta=StrictEnvelopeFactory._make_meta(meta, produced_by, trace_id)
        )
    
    @staticmethod
    def error(
        error_msg: str,
        *,
        error_type: str = "ExecutionError",
        produced_by: str | None = None,
        trace_id: str | None = None,
        meta: dict[str, Any] | None = None
    ) -> Envelope:
        """Create an error envelope with strict validation.
        
        Args:
            error_msg: Error message
            error_type: Type of error
            produced_by: Node or component that produced this error
            trace_id: Execution trace ID
            meta: Additional metadata
            
        Returns:
            Text envelope with error metadata
        """
        if not isinstance(error_msg, str):
            error_msg = str(error_msg)
        
        error_meta = StrictEnvelopeFactory._make_meta(meta, produced_by, trace_id)
        error_meta["error"] = error_msg
        error_meta["error_type"] = error_type
        error_meta["is_error"] = True
        
        return Envelope(
            content_type=ContentType.RAW_TEXT,
            body=error_msg,
            produced_by=produced_by or "system",
            trace_id=trace_id or "",
            meta=error_meta
        )


def get_envelope_factory() -> type[EnvelopeFactory] | type[StrictEnvelopeFactory]:
    """Get the appropriate envelope factory based on environment configuration.
    
    Returns:
        StrictEnvelopeFactory if DIPEO_STRICT_ENVELOPE=1, else EnvelopeFactory
    """
    if os.getenv("DIPEO_STRICT_ENVELOPE") == "1":
        logger.info("Using StrictEnvelopeFactory (DIPEO_STRICT_ENVELOPE=1)")
        return StrictEnvelopeFactory
    return EnvelopeFactory


def get_fallback_stats() -> dict[str, int]:
    """Get current fallback conversion statistics.
    
    Returns:
        Dictionary with conversion type as key and count as value
    """
    return dict(_fallback_counters)


def reset_fallback_stats() -> None:
    """Reset fallback conversion counters."""
    global _fallback_counters
    _fallback_counters = defaultdict(int)
    logger.info("Fallback conversion counters reset")


def log_fallback_stats() -> None:
    """Log current fallback conversion statistics."""
    if not _fallback_counters:
        logger.info("No fallback conversions recorded")
        return
    
    logger.warning("Envelope fallback conversion statistics:")
    for conversion_type, count in sorted(_fallback_counters.items()):
        logger.warning(f"  {conversion_type}: {count}")
    
    total = sum(_fallback_counters.values())
    logger.warning(f"  Total fallback conversions: {total}")


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
    
    Only handles the standard Envelope format now that legacy support has been removed.
    """
    
    # Envelope format (with discriminator check for safety)
    if not (data.get("envelope_format") or data.get("_envelope_format")):
        raise ValueError(f"Invalid envelope data: missing envelope_format discriminator")
    
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