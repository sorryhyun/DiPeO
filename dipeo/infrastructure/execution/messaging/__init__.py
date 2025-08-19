"""Messaging adapter module."""

from .message_router import MessageRouter, message_router
from .event_bus import MessageRouterEventBusAdapter, MessageBusCompatibilityAdapter
from .in_memory_event_bus import InMemoryEventBus
from .observer_adapter import ObserverToEventAdapter
from .messaging_adapter import MessageBusAdapter
from .null_event_bus import NullEventBus

__all__ = [
    "MessageRouter",
    "message_router",
    "MessageRouterEventBusAdapter",
    "InMemoryEventBus",
    "ObserverToEventAdapter",
    "MessageBusAdapter",
    "MessageBusCompatibilityAdapter",
    "NullEventBus",
]