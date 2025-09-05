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

    def matches(self, event: DomainEvent) -> bool:
        """Check if an event matches the filter criteria.

        Args:
            event: The domain event to check

        Returns:
            True if the event matches the filter, False otherwise
        """
        ...


class EventHandler(Protocol, Generic[T]):
    """Protocol for handling domain events."""

    async def handle(self, event: T) -> None:
        """Handle a domain event."""
        ...


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
    """Unified event bus protocol for all domain event operations.

    This protocol consolidates the functionality of:
    - DomainEventBus: Core event publishing and subscription
    - EventEmitter: Simple event emission
    - EventConsumer: Event consumption
    - MessageBus: Execution-specific messaging

    Infrastructure implementations can provide:
    - In-memory event bus for single-process applications
    - Redis-based event bus for distributed systems
    - Kafka-based event bus for high-throughput scenarios
    """

    # Core Publishing
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event.

        This should be a fire-and-forget operation that doesn't block
        the publisher. Infrastructure should handle retries and failures.

        Args:
            event: The domain event to publish
        """
        ...

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events atomically.

        Either all events are published or none are.

        Args:
            events: List of domain events to publish
        """
        ...

    # Subscription Management
    async def subscribe(
        self,
        event_types: list[EventType],
        handler: EventHandler,
        filter: EventFilter | None = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> EventSubscription:
        """Subscribe to domain events.

        Args:
            event_types: Types of events to subscribe to
            handler: Handler to process events
            filter: Optional event filter to apply before handling
            priority: Priority for event processing

        Returns:
            Subscription object that can be used to unsubscribe
        """
        ...

    async def unsubscribe(self, subscription: EventSubscription) -> None:
        """Unsubscribe from domain events.

        Args:
            subscription: The subscription to cancel
        """
        ...

    # Lifecycle Management
    async def initialize(self) -> None:
        """Initialize the event bus.

        Infrastructure may need to establish connections,
        start background tasks, etc.
        """
        ...

    async def cleanup(self) -> None:
        """Stop the event bus and clean up resources.

        Should gracefully shut down, allowing in-flight
        events to be processed.
        """
        ...

    # Execution-Specific Operations (formerly MessageBus)
    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        """Register a connection handler for execution updates.

        Args:
            connection_id: Unique identifier for the connection
            handler: Callback to handle messages for this connection
        """
        ...

    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a connection.

        Args:
            connection_id: The connection to unregister
        """
        ...

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast message to all connections subscribed to an execution.

        Args:
            execution_id: The execution to broadcast to
            message: The message to broadcast
        """
        ...

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Subscribe a connection to execution updates.

        Args:
            connection_id: The connection to subscribe
            execution_id: The execution to subscribe to
        """
        ...

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Unsubscribe a connection from execution updates.

        Args:
            connection_id: The connection to unsubscribe
            execution_id: The execution to unsubscribe from
        """
        ...

    def get_stats(self) -> dict:
        """Get bus statistics.

        Returns:
            Dictionary containing bus metrics and status
        """
        ...


class EventStore(Protocol):
    """Optional port for event sourcing and audit logging.

    This remains separate from EventBus as it serves a different purpose:
    persistent storage of events for replay and audit.
    """

    async def append(self, event: DomainEvent) -> None:
        """Append an event to the event store."""
        ...

    async def get_events(
        self, aggregate_id: str, from_version: int | None = None, to_version: int | None = None
    ) -> list[DomainEvent]:
        """Retrieve events for an aggregate."""
        ...

    async def get_events_by_correlation(self, correlation_id: str) -> list[DomainEvent]:
        """Retrieve all events with a given correlation ID."""
        ...

    async def replay_events(
        self,
        from_timestamp: datetime,
        to_timestamp: datetime | None = None,
        event_types: list[EventType] | None = None,
    ) -> list[DomainEvent]:
        """Replay events within a time range."""
        ...


# Backward Compatibility Aliases (to be removed in v1.0)
DomainEventBus = EventBus
MessageBus = EventBus
EventEmitter = EventBus
EventConsumer = EventBus
