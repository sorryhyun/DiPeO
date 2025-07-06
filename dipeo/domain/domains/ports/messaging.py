"""Messaging port for domain layer."""

from collections.abc import Callable
from typing import Protocol, runtime_checkable


@runtime_checkable
class MessageRouterPort(Protocol):
    """Port for message routing infrastructure."""

    async def initialize(self) -> None:
        """Initialize the message router."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        """Register a connection handler."""
        ...

    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a connection."""
        ...

    async def route_to_connection(self, connection_id: str, message: dict) -> bool:
        """Route a message to a specific connection."""
        ...

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast a message to all connections subscribed to an execution."""
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
        """Get statistics about active connections and subscriptions."""
        ...
