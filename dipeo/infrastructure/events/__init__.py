"""Event infrastructure for DiPeO.

This module provides concrete implementations of domain event ports,
including event buses and event stores.
"""

from .serialize import serialize_for_json, event_to_json_payload

__all__ = [
    "serialize_for_json",
    "event_to_json_payload",
]