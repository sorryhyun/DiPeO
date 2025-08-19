"""Event bus infrastructure adapters."""

from .domain_event_bus_adapter import DomainEventBusAdapter
from .in_memory_event_bus import InMemoryEventBus
from .message_router_event_bus import MessageRouterEventBusAdapter, MessageBusCompatibilityAdapter
from .redis_event_bus import RedisEventBus
from .observer_to_event_adapter import ObserverToEventAdapter
from .legacy import AsyncEventBus, NullEventBus

__all__ = [
    "DomainEventBusAdapter",
    "InMemoryEventBus",
    "MessageRouterEventBusAdapter",
    "MessageBusCompatibilityAdapter",
    "RedisEventBus",
    "ObserverToEventAdapter",
    # Legacy exports for backward compatibility
    "AsyncEventBus",
    "NullEventBus",
]