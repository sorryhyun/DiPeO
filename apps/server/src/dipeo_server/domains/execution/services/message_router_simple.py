"""Simplified message router for single-worker deployment without Redis."""

import asyncio
import logging
from typing import Callable, Dict, Set

logger = logging.getLogger(__name__)


class SimpleMessageRouter:
    """
    Simple in-memory message router for single-worker deployment.
    Replaces Redis-based MessageRouter for simpler deployments.
    """

    def __init__(self):
        self.worker_id = "single-worker"
        self.local_handlers: Dict[str, Callable] = {}
        self.execution_subscriptions: Dict[
            str, Set[str]
        ] = {}  # execution_id -> set of connection_ids
        self._initialized = False

    async def initialize(self):
        """Initialize the router (no-op for simple router)"""
        if self._initialized:
            return

        self._initialized = True
        logger.info(f"SimpleMessageRouter initialized for {self.worker_id}")

    async def cleanup(self):
        """Clean up resources"""
        self.local_handlers.clear()
        self.execution_subscriptions.clear()
        self._initialized = False

    async def register_connection(self, connection_id: str, handler: Callable):
        """Register a connection handler"""
        self.local_handlers[connection_id] = handler
        logger.debug(f"Registered connection {connection_id}")

    async def unregister_connection(self, connection_id: str):
        """Unregister a connection handler"""
        self.local_handlers.pop(connection_id, None)

        # Remove from all execution subscriptions
        for exec_id, connections in list(self.execution_subscriptions.items()):
            connections.discard(connection_id)
            if not connections:
                del self.execution_subscriptions[exec_id]

        logger.debug(f"Unregistered connection {connection_id}")

    async def route_to_connection(self, connection_id: str, message: dict) -> bool:
        """Route a message to a specific connection"""
        handler = self.local_handlers.get(connection_id)
        if handler:
            try:
                await handler(message)
                return True
            except Exception as e:
                logger.error(f"Error delivering message to {connection_id}: {e}")
                # Remove dead connection
                await self.unregister_connection(connection_id)
                return False
        else:
            logger.warning(f"No handler for connection {connection_id}")
            return False

    async def broadcast_to_execution(self, execution_id: str, message: dict):
        """Broadcast a message to all connections subscribed to an execution"""
        connection_ids = self.execution_subscriptions.get(execution_id, set())

        if not connection_ids:
            logger.debug(f"No subscribers for execution {execution_id}")
            return

        # Send to all subscribed connections
        tasks = []
        for conn_id in list(
            connection_ids
        ):  # Copy to avoid modification during iteration
            tasks.append(self.route_to_connection(conn_id, message))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Log any failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to broadcast to connection: {result}")

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ):
        """Subscribe a connection to execution updates"""
        if execution_id not in self.execution_subscriptions:
            self.execution_subscriptions[execution_id] = set()

        self.execution_subscriptions[execution_id].add(connection_id)
        logger.debug(f"Subscribed {connection_id} to execution {execution_id}")

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ):
        """Unsubscribe a connection from execution updates"""
        if execution_id in self.execution_subscriptions:
            self.execution_subscriptions[execution_id].discard(connection_id)

            # Clean up empty subscription sets
            if not self.execution_subscriptions[execution_id]:
                del self.execution_subscriptions[execution_id]

        logger.debug(f"Unsubscribed {connection_id} from execution {execution_id}")

    def get_stats(self) -> dict:
        """Get router statistics"""
        return {
            "worker_id": self.worker_id,
            "active_connections": len(self.local_handlers),
            "active_executions": len(self.execution_subscriptions),
            "total_subscriptions": sum(
                len(conns) for conns in self.execution_subscriptions.values()
            ),
        }


# Global instance for single-worker deployment
message_router = SimpleMessageRouter()
