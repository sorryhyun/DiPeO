"""Event serialization utilities for JSON streaming.

This module provides centralized serialization for domain events,
ensuring consistent format across all transport mechanisms.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID
import json
from dipeo.domain.events import DomainEvent


def serialize_for_json(data: dict[str, Any]) -> dict[str, Any]:
    """Serialize event data for JSON transport.
    
    Converts domain event data into a JSON-serializable format,
    handling special types like UUID, datetime, etc.
    
    Args:
        data: Event data to serialize
        
    Returns:
        JSON-serializable dictionary
    """
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
        elif hasattr(value, '__dict__'):
            # Handle dataclass-like objects
            return convert_value(value.__dict__)
        else:
            return value
    
    return convert_value(data)


def event_to_json_payload(event: 'DomainEvent') -> dict[str, Any]:
    """Convert a DomainEvent to JSON-serializable payload.
    
    Args:
        event: Domain event to serialize
        
    Returns:
        JSON-serializable dictionary with standard event structure
    """
    from dipeo.domain.events.contracts import DomainEvent
    
    return serialize_for_json({
        "type": event.type.value,
        "execution_id": str(event.scope.execution_id) if event.scope.execution_id else None,
        "node_id": event.scope.node_id,
        "data": event.payload,
        "timestamp": event.occurred_at.isoformat(),
        "correlation_id": event.correlation_id,
        "metadata": event.meta
    })