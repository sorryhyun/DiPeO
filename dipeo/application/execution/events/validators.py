"""Event validation utilities for ensuring event data integrity."""

from typing import Any

from dipeo.domain.events import DomainEvent, EventType


def validate_event_metadata(event: DomainEvent) -> bool:
    """Validate that event has required metadata.

    Args:
        event: Event to validate

    Returns:
        True if event metadata is valid
    """
    if not event.scope:
        return False

    if not event.scope.execution_id:
        return False

    return True


def validate_node_event_payload(payload: dict[str, Any]) -> bool:
    """Validate node event payload has required fields.

    Args:
        payload: Event payload to validate

    Returns:
        True if payload is valid
    """
    required_fields = {"node_id", "execution_id"}
    return all(field in payload for field in required_fields)


def validate_execution_event_payload(payload: dict[str, Any]) -> bool:
    """Validate execution event payload has required fields.

    Args:
        payload: Event payload to validate

    Returns:
        True if payload is valid
    """
    return "execution_id" in payload


def is_critical_event(event_type: EventType) -> bool:
    """Check if event type is critical and should not be dropped.

    Args:
        event_type: Type of event to check

    Returns:
        True if event is critical
    """
    critical_types = {
        EventType.EXECUTION_STARTED,
        EventType.EXECUTION_COMPLETED,
        EventType.EXECUTION_FAILED,
        EventType.NODE_FAILED,
    }
    return event_type in critical_types
