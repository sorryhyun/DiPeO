"""Domain ports for messaging and event bus."""

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable


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


@runtime_checkable
class DomainEventBus(Protocol):
    """Event bus for domain events."""

    async def publish(self, event: "DomainEvent") -> None:
        """Publish a domain event."""
        ...

    async def subscribe(
        self, event_type: type["DomainEvent"], handler: Callable[[Any], None]
    ) -> None:
        """Subscribe to a domain event type."""
        ...

    async def unsubscribe(
        self, event_type: type["DomainEvent"], handler: Callable[[Any], None]
    ) -> None:
        """Unsubscribe from a domain event type."""
        ...