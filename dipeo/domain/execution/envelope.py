from __future__ import annotations

import io
import json
import logging
import os
import time
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import uuid4

from dipeo.diagram_generated.enums import ContentType

if TYPE_CHECKING:
    import numpy as np

T = TypeVar("T")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Envelope:
    """Immutable message envelope for inter-node communication."""

    id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: str = field(default="")
    produced_by: str = field(default="system")
    content_type: ContentType = field(default="raw_text")
    schema_id: str | None = field(default=None)
    serialization_format: str | None = field(default=None)
    body: Any = field(default=None)
    meta: dict[str, Any] = field(default_factory=dict)

    def with_meta(self, **kwargs) -> Envelope:
        new_meta = {**self.meta, **kwargs}
        return replace(self, meta=new_meta)

    def with_iteration(self, iteration: int) -> Envelope:
        return self.with_meta(iteration=iteration)

    def with_branch(self, branch_id: str) -> Envelope:
        return self.with_meta(branch_id=branch_id)

    @property
    def error(self) -> str | None:
        return self.meta.get("error")

    def has_error(self) -> bool:
        return "error" in self.meta and self.meta["error"] is not None

    def as_text(self) -> str:
        if self.content_type == ContentType.RAW_TEXT:
            return str(self.body) if self.body is not None else ""
        else:
            raise ValueError(
                f"Cannot convert {self.content_type} to text - use to_text() for strict checking"
            )

    def as_json(self, model: type[T] | None = None) -> T | dict | list:
        if self.content_type != ContentType.OBJECT:
            raise ValueError(
                f"Cannot extract JSON from {self.content_type} - use to_json() for strict checking"
            )

        data = self.body

        # Validate with Pydantic if model provided
        if model:
            try:
                from pydantic import BaseModel, ValidationError

                if issubclass(model, BaseModel):
                    return model.model_validate(data)
            except (ImportError, ValidationError) as e:
                raise ValueError(f"Schema validation failed: {e}") from e

        return data

    def as_bytes(self) -> bytes:
        if self.content_type == ContentType.BINARY:
            if isinstance(self.body, bytes):
                return self.body
            else:
                raise ValueError(f"Binary envelope contains non-bytes data: {type(self.body)}")
        else:
            raise ValueError(
                f"Cannot extract binary from {self.content_type} - use to_bytes() for strict checking"
            )

    def as_conversation(self) -> dict:
        if self.content_type != ContentType.CONVERSATION_STATE:
            raise ValueError(f"Expected conversation_state, got {self.content_type}")
        return self.body

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
                raise TypeError(f"OBJECT body must be JSON-serializable: {e}") from e
        return self.body

    def to_bytes(self) -> bytes:
        if self.content_type is not ContentType.BINARY:
            raise TypeError(f"Envelope is not BINARY, got {self.content_type}")
        if not isinstance(self.body, bytes | bytearray | memoryview):
            raise TypeError(f"BINARY body must be bytes-like, got {type(self.body)}")
        return bytes(self.body)


class EnvelopeFactory:
    @staticmethod
    def numpy_array(array: np.ndarray, **kwargs) -> Envelope:
        import numpy as np

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
                "size": array.size,
            },
            **kwargs,
        )

    @staticmethod
    def create(
        body: Any,
        content_type: ContentType | None = None,
        node_id: str | None = None,
        error: str | None = None,
        **kwargs,
    ) -> Envelope:
        """Generic factory method for creating envelopes with auto-detection.

        Args:
            body: The content to wrap in the envelope
            content_type: Optional explicit content type. If None, will auto-detect from body
            node_id: Optional node ID for backward compatibility
            error: Optional error type. If provided, creates an error envelope
            **kwargs: Additional envelope attributes

        Returns:
            Envelope with appropriate content type
        """
        meta = kwargs.pop("meta", {})
        meta["timestamp"] = meta.get("timestamp", time.time())

        if node_id:
            kwargs.setdefault("produced_by", node_id)

        if error:
            meta["is_error"] = True
            meta["error"] = body if isinstance(body, str) else str(body)
            meta["error_type"] = error
            if content_type is None:
                content_type = ContentType.RAW_TEXT

        if content_type is None:
            if isinstance(body, str):
                content_type = ContentType.RAW_TEXT
            elif isinstance(body, bytes | bytearray | memoryview):
                content_type = ContentType.BINARY
            elif isinstance(body, dict | list):
                content_type = ContentType.OBJECT
            else:
                content_type = ContentType.OBJECT

        return Envelope(content_type=content_type, body=body, meta=meta, **kwargs)


class StrictEnvelopeFactory:
    """Strict envelope factory with no implicit conversions or fallbacks.

    This factory enforces:
    - Explicit content type matching
    - Type validation at creation time
    - Required metadata fields
    - No auto-coercion between types
    """

    @staticmethod
    def _make_meta(meta: dict[str, Any] | None, *_unused) -> dict[str, Any]:
        result = meta.copy() if meta else {}
        result["timestamp"] = result.get("timestamp", time.time())
        return result

    @staticmethod
    def text(
        content: str,
        *,
        produced_by: str | None = None,
        trace_id: str | None = None,
        meta: dict[str, Any] | None = None,
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
            meta=StrictEnvelopeFactory._make_meta(meta, produced_by, trace_id),
        )

    @staticmethod
    def json(
        value: Any,
        *,
        produced_by: str | None = None,
        trace_id: str | None = None,
        meta: dict[str, Any] | None = None,
        schema_id: str | None = None,
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
            raise TypeError(f"json() requires JSON-serializable value: {e}") from e

        return Envelope(
            content_type=ContentType.OBJECT,
            body=value,
            schema_id=schema_id,
            produced_by=produced_by or "system",
            trace_id=trace_id or "",
            meta=StrictEnvelopeFactory._make_meta(meta, produced_by, trace_id),
        )

    @staticmethod
    def binary(
        data: bytes | bytearray | memoryview,
        *,
        produced_by: str | None = None,
        trace_id: str | None = None,
        meta: dict[str, Any] | None = None,
        format: str = "raw",
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
        if not isinstance(data, bytes | bytearray | memoryview):
            raise TypeError(f"binary() requires bytes-like data, got {type(data)}")

        return Envelope(
            content_type=ContentType.BINARY,
            body=bytes(data),  # Convert to bytes for consistency
            serialization_format=format,
            produced_by=produced_by or "system",
            trace_id=trace_id or "",
            meta=StrictEnvelopeFactory._make_meta(meta, produced_by, trace_id),
        )

    @staticmethod
    def conversation(
        state: dict,
        *,
        produced_by: str | None = None,
        trace_id: str | None = None,
        meta: dict[str, Any] | None = None,
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
            meta=StrictEnvelopeFactory._make_meta(meta, produced_by, trace_id),
        )

    @staticmethod
    def error(
        error_msg: str,
        *,
        error_type: str = "ExecutionError",
        produced_by: str | None = None,
        trace_id: str | None = None,
        meta: dict[str, Any] | None = None,
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
            meta=error_meta,
        )


def get_envelope_factory() -> type[EnvelopeFactory] | type[StrictEnvelopeFactory]:
    if os.getenv("DIPEO_STRICT_ENVELOPE") == "1":
        logger.info("Using StrictEnvelopeFactory (DIPEO_STRICT_ENVELOPE=1)")
        return StrictEnvelopeFactory
    return EnvelopeFactory


def serialize_protocol(output: Envelope) -> dict[str, Any]:
    return {
        "envelope_format": True,
        "id": output.id,
        "trace_id": output.trace_id,
        "produced_by": output.produced_by,
        "content_type": output.content_type.value
        if hasattr(output.content_type, "value")
        else output.content_type,
        "schema_id": output.schema_id,
        "serialization_format": output.serialization_format,
        "body": output.body,
        "meta": output.meta,
    }


def deserialize_protocol(data: dict[str, Any]) -> Envelope:
    if not (data.get("envelope_format") or data.get("_envelope_format")):
        raise ValueError("Invalid envelope data: missing envelope_format discriminator")

    content_type_val = data.get("content_type", "raw_text")

    if isinstance(content_type_val, str):
        try:
            content_type = ContentType(content_type_val)
        except (ValueError, KeyError):
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
        meta=data.get("meta", {}),
    )
