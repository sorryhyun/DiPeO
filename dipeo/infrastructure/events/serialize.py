"""Event serialization for JSON streaming with consistent format."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from dipeo.domain.events import DomainEvent


def serialize_for_json(data: dict[str, Any]) -> dict[str, Any]:
    """Convert domain event data to JSON-serializable format (handles UUID, datetime, Enum)."""

    def convert_value(value: Any) -> Any:
        if isinstance(value, UUID):
            return str(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, Enum):
            return value.value
        elif isinstance(value, dict):
            return {k: convert_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [convert_value(v) for v in value]
        elif hasattr(value, "model_dump"):
            return convert_value(value.model_dump())
        elif hasattr(value, "__dict__"):
            return convert_value(value.__dict__)
        else:
            return value

    return convert_value(data)


def event_to_json_payload(event: "DomainEvent") -> dict[str, Any]:
    payload_data = None
    if event.payload is not None:
        import dataclasses

        if dataclasses.is_dataclass(event.payload):
            payload_data = dataclasses.asdict(event.payload)
        elif hasattr(event.payload, "model_dump"):
            payload_data = event.payload.model_dump()
        elif hasattr(event.payload, "__dict__"):
            payload_data = event.payload.__dict__
        else:
            payload_data = event.payload

    return serialize_for_json(
        {
            "type": event.type.value,
            "execution_id": str(event.scope.execution_id) if event.scope.execution_id else None,
            "node_id": event.scope.node_id,
            "data": payload_data,
            "timestamp": event.occurred_at.isoformat(),
            "correlation_id": event.correlation_id,
            "metadata": event.meta,
        }
    )
