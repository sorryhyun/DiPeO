"""Message router implementation for real-time event distribution.

This module provides the central message routing infrastructure that distributes
execution events to various consumers (SSE, WebSocket, GraphQL subscriptions, etc.)
"""

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from dipeo.core.ports import MessageRouterPort

logger = logging.getLogger(__name__)


@dataclass
class ConnectionHealth:
    """Health metrics for a connection."""

    last_successful_send: float
    failed_attempts: int = 0
    total_messages: int = 0
    avg_latency: float = 0.0


class MessageRouter(MessageRouterPort):
    """Central message router implementing the MessageRouterPort protocol.

    This router manages connections and routes execution events to appropriate
    consumers. It serves as the single source of truth for real-time monitoring,
    supporting multiple transport mechanisms including:
    - Server-Sent Events (SSE)
    - WebSocket connections
    - GraphQL subscriptions
    - Future transport mechanisms

    The router includes health monitoring, backpressure handling, and automatic
    cleanup of failed connections.
    """

    def __init__(self):
        self.worker_id = "single-worker"
        self.local_handlers: dict[str, Callable] = {}
        self.execution_subscriptions: dict[str, set[str]] = {}
        self._initialized = False
        self.connection_health: dict[str, ConnectionHealth] = {}
        self._message_queue_size: dict[str, int] = {}
        self._queue_lock = threading.Lock()
        self.max_queue_size = 100

    async def initialize(self) -> None:
        """Initialize the message router."""
        if self._initialized:
            return

        self._initialized = True
        logger.info("MessageRouter initialized")

    async def cleanup(self) -> None:
        """Clean up all connections and subscriptions."""
        self.local_handlers.clear()
        self.execution_subscriptions.clear()
        self.connection_health.clear()
        self._message_queue_size.clear()
        self._initialized = False
        logger.info("MessageRouter cleaned up")

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        """Register a new connection with its message handler.

        Args:
            connection_id: Unique identifier for the connection
            handler: Async callable that will receive messages for this connection
        """
        self.local_handlers[connection_id] = handler
        self.connection_health[connection_id] = ConnectionHealth(last_successful_send=time.time())
        self._message_queue_size[connection_id] = 0
        logger.debug(f"Registered connection: {connection_id}")

    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a connection and clean up its subscriptions.

        Args:
            connection_id: Connection identifier to remove
        """
        self.local_handlers.pop(connection_id, None)
        self.connection_health.pop(connection_id, None)
        self._message_queue_size.pop(connection_id, None)

        # Remove from all execution subscriptions
        for exec_id, connections in list(self.execution_subscriptions.items()):
            connections.discard(connection_id)
            if not connections:
                del self.execution_subscriptions[exec_id]

        logger.debug(f"Unregistered connection: {connection_id}")

    async def route_to_connection(self, connection_id: str, message: dict) -> bool:
        """Route a message to a specific connection.

        Args:
            connection_id: Target connection identifier
            message: Message to deliver

        Returns:
            True if message was delivered successfully, False otherwise
        """
        handler = self.local_handlers.get(connection_id)
        if not handler:
            logger.warning(f"No handler for connection {connection_id}")
            return False

        # Check queue size for backpressure
        with self._queue_lock:
            queue_size = self._message_queue_size.get(connection_id, 0)
            if queue_size > self.max_queue_size:
                logger.warning(
                    f"Connection {connection_id} queue full ({queue_size} messages), "
                    f"applying backpressure"
                )
                return False
            self._message_queue_size[connection_id] = queue_size + 1

        start_time = time.time()
        try:
            await handler(message)

            # Update health metrics
            latency = time.time() - start_time
            health = self.connection_health.get(connection_id)
            if health:
                health.last_successful_send = time.time()
                health.total_messages += 1
                health.avg_latency = (
                    health.avg_latency * (health.total_messages - 1) + latency
                ) / health.total_messages
                health.failed_attempts = 0

            return True

        except Exception as e:
            logger.error(f"Error delivering message to {connection_id}: {e}")

            # Update failure metrics
            health = self.connection_health.get(connection_id)
            if health:
                health.failed_attempts += 1
                if health.failed_attempts > 3:
                    logger.error(
                        f"Connection {connection_id} exceeded failure threshold, unregistering"
                    )
                    await self.unregister_connection(connection_id)

            return False

        finally:
            # Update queue size
            with self._queue_lock:
                self._message_queue_size[connection_id] = max(
                    0, self._message_queue_size.get(connection_id, 1) - 1
                )

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast a message to all connections subscribed to an execution.

        Args:
            execution_id: Execution identifier
            message: Message to broadcast
        """
        start_time = time.time()

        # Try to publish to GraphQL subscriptions (if available)
        try:
            from dipeo_server.api.graphql.subscriptions import publish_execution_update

            await publish_execution_update(execution_id, message)
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Failed to publish to streaming manager: {e}")

        # Get all connections subscribed to this execution
        connection_ids = self.execution_subscriptions.get(execution_id, set())

        if not connection_ids:
            return

        successful_broadcasts = 0
        failed_broadcasts = 0

        # Use TaskGroup for Python 3.11+ or gather for older versions
        import sys

        if sys.version_info >= (3, 11):
            try:

                async def track_broadcast(connection_id: str, msg: dict):
                    broadcast_result = await self._broadcast_with_metrics(connection_id, msg)
                    return connection_id, broadcast_result

                results = []
                async with asyncio.TaskGroup() as tg:
                    for conn_id in list(connection_ids):
                        task = tg.create_task(track_broadcast(conn_id, message))
                        results.append(task)

                for task in results:
                    try:
                        conn_id, success = task.result()
                        if success:
                            successful_broadcasts += 1
                        else:
                            failed_broadcasts += 1
                    except Exception as e:
                        logger.error(f"Broadcast error: {e}")
                        failed_broadcasts += 1

            except Exception as e:
                logger.error(f"TaskGroup error during broadcast: {e}")
                failed_broadcasts = len(connection_ids)
        else:
            tasks = []
            for conn_id in list(connection_ids):
                tasks.append(self._broadcast_with_metrics(conn_id, message))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Failed to broadcast to connection: {result}")
                        failed_broadcasts += 1
                    elif result:
                        successful_broadcasts += 1

        # Log slow broadcasts
        broadcast_time = time.time() - start_time
        if broadcast_time > 0.1:
            logger.warning(
                f"Slow broadcast to execution {execution_id}: "
                f"{broadcast_time:.2f}s for {len(connection_ids)} connections "
                f"(success: {successful_broadcasts}, failed: {failed_broadcasts})"
            )

    async def _broadcast_with_metrics(self, conn_id: str, message: dict) -> bool:
        """Helper method to broadcast with metrics tracking.

        Args:
            conn_id: Connection identifier
            message: Message to send

        Returns:
            True if broadcast succeeded
        """
        result = await self.route_to_connection(conn_id, message)
        return result

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Subscribe a connection to receive updates for a specific execution.

        Args:
            connection_id: Connection identifier
            execution_id: Execution to subscribe to
        """
        if execution_id not in self.execution_subscriptions:
            self.execution_subscriptions[execution_id] = set()

        self.execution_subscriptions[execution_id].add(connection_id)
        logger.debug(f"Subscribed {connection_id} to execution {execution_id}")

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Unsubscribe a connection from an execution.

        Args:
            connection_id: Connection identifier
            execution_id: Execution to unsubscribe from
        """
        if execution_id in self.execution_subscriptions:
            self.execution_subscriptions[execution_id].discard(connection_id)

            # Clean up empty subscription sets
            if not self.execution_subscriptions[execution_id]:
                del self.execution_subscriptions[execution_id]

        logger.debug(f"Unsubscribed {connection_id} from execution {execution_id}")

    def get_stats(self) -> dict:
        """Get router statistics and health metrics.

        Returns:
            Dictionary containing router stats and connection health
        """
        now = time.time()
        unhealthy_connections = [
            conn_id
            for conn_id, health in self.connection_health.items()
            if now - health.last_successful_send > 60
        ]

        avg_queue_size = (
            sum(self._message_queue_size.values()) / len(self._message_queue_size)
            if self._message_queue_size
            else 0
        )

        return {
            "worker_id": self.worker_id,
            "active_connections": len(self.local_handlers),
            "active_executions": len(self.execution_subscriptions),
            "total_subscriptions": sum(
                len(conns) for conns in self.execution_subscriptions.values()
            ),
            "unhealthy_connections": len(unhealthy_connections),
            "avg_queue_size": round(avg_queue_size, 2),
            "connection_health": {
                conn_id: {
                    "last_send": datetime.fromtimestamp(health.last_successful_send).isoformat(),
                    "failed_attempts": health.failed_attempts,
                    "total_messages": health.total_messages,
                    "avg_latency_ms": round(health.avg_latency * 1000, 2),
                }
                for conn_id, health in self.connection_health.items()
            },
        }


# Singleton instance for backward compatibility
message_router = MessageRouter()
