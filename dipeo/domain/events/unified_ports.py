"""Unified event bus protocol for domain event handling.

This module consolidates all event-related protocols into a single, focused EventBus protocol
following the Interface Segregation Principle.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Protocol, TypeVar, runtime_checkable

from .contracts import DomainEvent
from .types import EventPriority, EventType

T = TypeVar("T", bound=DomainEvent)


class EventFilter(Protocol):
    """Protocol for filtering domain events."""

    def matches(self, event: DomainEvent) -> bool: ...


class EventHandler[T](Protocol):
    """Protocol for handling domain events."""

    async def handle(self, event: T) -> None: ...


@dataclass
class EventSubscription:
    """Represents a subscription to domain events."""

    subscription_id: str
    event_types: list[EventType]
    handler: EventHandler
    filter: EventFilter | None = None
    priority: EventPriority = EventPriority.NORMAL
    active: bool = True


@runtime_checkable
class EventBus(Protocol):
    """Unified event bus protocol for all domain event operations."""

    async def publish(self, event: DomainEvent) -> None: ...

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events atomically."""
        ...

    async def subscribe(
        self,
        event_types: list[EventType],
        handler: EventHandler,
        filter: EventFilter | None = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> EventSubscription: ...

    async def unsubscribe(self, subscription: EventSubscription) -> None: ...

    async def initialize(self) -> None: ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        """Register a connection handler for execution updates."""
        ...

    async def unregister_connection(self, connection_id: str) -> None: ...

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast message to all connections subscribed to execution."""
        ...

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None: ...

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None: ...

    def get_stats(self) -> dict: ...


class EventStore(Protocol):
    """Optional port for event sourcing and audit logging."""

    async def append(self, event: DomainEvent) -> None: ...

    async def get_events(
        self, aggregate_id: str, from_version: int | None = None, to_version: int | None = None
    ) -> list[DomainEvent]: ...

    async def get_events_by_correlation(self, correlation_id: str) -> list[DomainEvent]: ...

    async def replay_events(
        self,
        from_timestamp: datetime,
        to_timestamp: datetime | None = None,
        event_types: list[EventType] | None = None,
    ) -> list[DomainEvent]: ...
