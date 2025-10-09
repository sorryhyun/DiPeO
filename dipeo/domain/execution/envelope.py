from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import uuid4

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.enums import ContentType

if TYPE_CHECKING:
    import numpy as np

T = TypeVar("T")

logger = get_module_logger(__name__)


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
