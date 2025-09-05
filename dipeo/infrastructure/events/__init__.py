"""Event infrastructure for DiPeO.

This module provides concrete implementations of domain event ports,
including event buses and event stores.
"""

from .serialize import event_to_json_payload, serialize_for_json

__all__ = [
    "event_to_json_payload",
    "serialize_for_json",
]
