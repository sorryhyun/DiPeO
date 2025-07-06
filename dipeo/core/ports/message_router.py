"""Message Router port interface."""

from collections.abc import Callable
from typing import Protocol, runtime_checkable


@runtime_checkable
class MessageRouterPort(Protocol):
    """Port for message routing infrastructure.
    
    This interface defines the contract for real-time message routing,
    supporting WebSocket connections and execution subscriptions.
    """

    async def initialize(self) -> None:
        """Initialize the message router."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        """Register a connection handler.
        
        Args:
            connection_id: Unique identifier for the connection
            handler: Async callable to handle messages for this connection
        """
        ...

    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a connection.
        
        Args:
            connection_id: Connection to unregister
        """
        ...

    async def route_to_connection(self, connection_id: str, message: dict) -> bool:
        """Route a message to a specific connection.
        
        Args:
            connection_id: Target connection ID
            message: Message to send
            
        Returns:
            True if message was delivered, False otherwise
        """
        ...

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast a message to all connections subscribed to an execution.
        
        Args:
            execution_id: Execution ID to broadcast to
            message: Message to broadcast
        """
        ...

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Subscribe a connection to execution updates.
        
        Args:
            connection_id: Connection to subscribe
            execution_id: Execution to subscribe to
        """
        ...

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Unsubscribe a connection from execution updates.
        
        Args:
            connection_id: Connection to unsubscribe
            execution_id: Execution to unsubscribe from
        """
        ...

    def get_stats(self) -> dict:
        """Get statistics about active connections and subscriptions.
        
        Returns:
            Dictionary with connection and subscription stats
        """
        ...