"""Event bus adapters for different infrastructure scenarios.

This module provides concrete implementations of the EventBus port:
- InMemoryEventBus: For single-process applications
- RedisEventBus: For distributed multi-worker deployments (TODO)
"""

from .in_memory_event_bus import InMemoryEventBus

__all__ = [
    "InMemoryEventBus",
]
