"""Port interfaces for domain event handling."""

from abc import ABC, abstractmethod
from typing import Callable, Protocol, Optional, TypeVar, Generic, runtime_checkable
from dataclasses import dataclass
from datetime import datetime

from .contracts import DomainEvent
from .types import EventType, EventPriority


T = TypeVar('T', bound=DomainEvent)


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
    filter: Optional[EventFilter] = None  # Event filter instance
    filter_expression: Optional[str] = None  # Legacy: string expression for backward compat
    priority: EventPriority = EventPriority.NORMAL
    active: bool = True


class DomainEventBus(Protocol):
    """Port interface for domain event bus.
    
    Infrastructure implementations can provide:
    - In-memory event bus for single-process applications
    - Redis-based event bus for distributed systems
    - Kafka-based event bus for high-throughput scenarios
    """
    
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
    
    async def subscribe(
        self,
        event_types: list[EventType],
        handler: EventHandler,
        filter: Optional[EventFilter] = None,
        filter_expression: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL
    ) -> EventSubscription:
        """Subscribe to domain events.
        
        Args:
            event_types: Types of events to subscribe to
            handler: Handler to process events
            filter: Optional event filter to apply before handling
            filter_expression: Legacy: Optional filter expression (infrastructure-specific)
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
    
    async def start(self) -> None:
        """Start the event bus.
        
        Infrastructure may need to establish connections,
        start background tasks, etc.
        """
        ...
    
    async def stop(self) -> None:
        """Stop the event bus and clean up resources.
        
        Should gracefully shut down, allowing in-flight
        events to be processed.
        """
        ...


class EventStore(Protocol):
    """Optional port for event sourcing and audit logging."""
    
    async def append(self, event: DomainEvent) -> None:
        """Append an event to the event store."""
        ...
    
    async def get_events(
        self,
        aggregate_id: str,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None
    ) -> list[DomainEvent]:
        """Retrieve events for an aggregate."""
        ...
    
    async def get_events_by_correlation(
        self,
        correlation_id: str
    ) -> list[DomainEvent]:
        """Retrieve all events with a given correlation ID."""
        ...
    
    async def replay_events(
        self,
        from_timestamp: datetime,
        to_timestamp: Optional[datetime] = None,
        event_types: Optional[list[EventType]] = None
    ) -> list[DomainEvent]:
        """Replay events within a time range."""
        ...


class EventEmitter(Protocol):
    """Protocol for emitting domain events."""
    
    async def emit(self, event: DomainEvent) -> None:
        """Emit a domain event."""
        ...


class EventConsumer(Protocol):
    """Protocol for consuming domain events."""
    
    async def consume(self, event: DomainEvent) -> None:
        """Consume a domain event."""
        ...


@runtime_checkable
class MessageBus(Protocol):
    """Message bus for execution updates and events."""

    async def initialize(self) -> None:
        """Initialize the message bus."""
        ...

    async def cleanup(self) -> None:
        """Cleanup resources."""
        ...

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        """Register a connection handler."""
        ...

    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a connection."""
        ...

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast message to all connections subscribed to an execution."""
        ...

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Subscribe a connection to execution updates."""
        ...

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Unsubscribe a connection from execution updates."""
        ...

    def get_stats(self) -> dict:
        """Get bus statistics."""
        ...