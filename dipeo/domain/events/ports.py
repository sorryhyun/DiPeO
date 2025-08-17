"""Port interfaces for domain event handling."""

from abc import ABC, abstractmethod
from typing import Callable, Protocol, Optional, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime

from .contracts import DomainEvent
from .types import EventType, EventPriority


T = TypeVar('T', bound=DomainEvent)


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
    filter_expression: Optional[str] = None  # e.g., "execution_id == 'xyz'"
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
        filter_expression: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL
    ) -> EventSubscription:
        """Subscribe to domain events.
        
        Args:
            event_types: Types of events to subscribe to
            handler: Handler to process events
            filter_expression: Optional filter expression (infrastructure-specific)
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


from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol
from .contracts import ExecutionEvent


class EventEmitter(Protocol):
    async def emit(self, event: ExecutionEvent) -> None: ...


class EventConsumer(Protocol):
    async def consume(self, event: ExecutionEvent) -> None: ...