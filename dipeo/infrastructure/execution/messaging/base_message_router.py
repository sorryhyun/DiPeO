"""Base message router with shared functionality for all router implementations.

This module provides the base implementation for message routing that is shared
between the in-memory and Redis-backed routers.
"""

import asyncio
import logging

from dipeo.config.base_logger import get_module_logger
import time
from abc import abstractmethod
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from dipeo.config import get_settings
from dipeo.domain.events import EventType
from dipeo.domain.events.contracts import DomainEvent
from dipeo.domain.events.unified_ports import EventBus as MessageRouterPort
from dipeo.domain.events.unified_ports import EventHandler
from dipeo.infrastructure.events.serialize import event_to_json_payload

logger = get_module_logger(__name__)

@dataclass
class ConnectionHealth:
    last_successful_send: float
    failed_attempts: int = 0
    total_messages: int = 0
    avg_latency: float = 0.0

class BaseMessageRouter(MessageRouterPort, EventHandler[DomainEvent]):
    """Base message router with shared functionality.

    This base class contains all the common logic for message routing including:
    - Connection management
    - Event buffering and replay
    - Batch processing
    - UI event transformation
    - Health monitoring

    Subclasses must implement broadcast_to_execution() to define their
    specific routing strategy (in-memory vs Redis).
    """

    def __init__(self):
        self.local_handlers: dict[str, Callable] = {}
        self.execution_subscriptions: dict[str, set[str]] = {}
        self.connection_health: dict[str, ConnectionHealth] = {}
        self._initialized = False

        # Load settings
        settings = get_settings()
        self.max_queue_size = settings.messaging.max_queue_size
        self._buffer_max_size = settings.messaging.buffer_max_per_exec
        self._buffer_ttl_seconds = settings.messaging.buffer_ttl_s
        self._batch_interval = settings.messaging.batch_interval_ms / 1000.0
        self._batch_max_size = settings.messaging.batch_max
        self._batch_broadcast_warning_threshold = settings.messaging.broadcast_warning_threshold_s

        # Event buffering
        self._event_buffer: dict[str, list[dict]] = {}

        # Batch processing
        self._batch_queue: dict[str, list[dict]] = {}
        self._batch_tasks: dict[str, asyncio.Task | None] = {}

        # Message queue tracking (for backpressure)
        self._message_queue_size: dict[str, int] = {}

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        """Register a new connection with its message handler.

        Args:
            connection_id: Unique identifier for the connection
            handler: Async callable that will receive messages for this connection
        """
        self.local_handlers[connection_id] = handler
        self.connection_health[connection_id] = ConnectionHealth(last_successful_send=time.time())
        self._message_queue_size[connection_id] = 0

    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a connection and clean up its subscriptions.

        Args:
            connection_id: Connection identifier to remove
        """
        self.local_handlers.pop(connection_id, None)
        self.connection_health.pop(connection_id, None)
        self._message_queue_size.pop(connection_id, None)

        for exec_id, connections in list(self.execution_subscriptions.items()):
            connections.discard(connection_id)
            if not connections:
                del self.execution_subscriptions[exec_id]

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

        # Check for backpressure
        import threading

        if not hasattr(self, "_queue_lock"):
            self._queue_lock = threading.Lock()

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
            with self._queue_lock:
                self._message_queue_size[connection_id] = max(
                    0, self._message_queue_size.get(connection_id, 1) - 1
                )

    @abstractmethod
    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast a message to all connections subscribed to an execution.

        This method must be implemented by subclasses to define their specific
        broadcast strategy (in-memory vs Redis).

        Args:
            execution_id: Execution identifier
            message: Message to broadcast
        """
        pass

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

        # Replay buffered events for late connections
        await self._replay_buffered_events(connection_id, execution_id)

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

            if not self.execution_subscriptions[execution_id]:
                del self.execution_subscriptions[execution_id]

    def _should_buffer_events(self, execution_id: str) -> bool:
        """Check if events should be buffered for an execution.

        Skip buffering for batch item executions to save memory.
        """
        return "_batch_" not in execution_id

    async def _buffer_event(self, execution_id: str, message: dict) -> None:
        """Buffer an event for late connections.

        Args:
            execution_id: Execution identifier
            message: Event message to buffer
        """
        if execution_id not in self._event_buffer:
            self._event_buffer[execution_id] = []

        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        self._event_buffer[execution_id].append(message)

        if len(self._event_buffer[execution_id]) > self._buffer_max_size:
            self._event_buffer[execution_id] = self._event_buffer[execution_id][
                -self._buffer_max_size :
            ]

    async def _replay_buffered_events(self, connection_id: str, execution_id: str) -> None:
        """Replay buffered events to a new connection.

        Args:
            connection_id: Connection to send events to
            execution_id: Execution whose events to replay
        """
        if execution_id not in self._event_buffer:
            return

        buffered_events = self._event_buffer.get(execution_id, [])
        if not buffered_events:
            return

        for event in buffered_events:
            event_type = event.get("type", "")
            if event_type in ["HEARTBEAT", "CONNECTION_ESTABLISHED"]:
                continue

            success = await self.route_to_connection(connection_id, event)
            if not success:
                logger.warning(f"Failed to replay event to connection {connection_id}")
                break

    async def _delayed_flush(self, execution_id: str) -> None:
        """Flush batch after a delay."""
        await asyncio.sleep(self._batch_interval)
        await self._flush_batch(execution_id)

    async def _flush_batch(self, execution_id: str) -> None:
        """Flush batched messages to connections."""
        messages = self._batch_queue.pop(execution_id, [])
        if execution_id in self._batch_tasks:
            self._batch_tasks[execution_id] = None

        if not messages:
            return

        connection_ids = self.execution_subscriptions.get(execution_id, set())
        if not connection_ids:
            return

        start_time = time.time()

        batch_message = {
            "type": "BATCH_UPDATE",
            "execution_id": execution_id,
            "events": messages,
            "timestamp": datetime.utcnow().isoformat(),
            "batch_size": len(messages),
        }

        # Try to publish to streaming manager if available
        try:
            from dipeo_server.api.graphql.subscriptions import publish_execution_update

            await publish_execution_update(execution_id, batch_message)
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Failed to publish batch to streaming manager: {e}")

        successful_broadcasts = 0
        failed_broadcasts = 0

        try:

            async def track_broadcast(connection_id: str, msg: dict):
                broadcast_result = await self._broadcast_with_metrics(connection_id, msg)
                return connection_id, broadcast_result

            results = []
            async with asyncio.TaskGroup() as tg:
                for conn_id in list(connection_ids):
                    task = tg.create_task(track_broadcast(conn_id, batch_message))
                    results.append(task)

            for task in results:
                try:
                    conn_id, success = task.result()
                    if success:
                        successful_broadcasts += 1
                    else:
                        failed_broadcasts += 1
                except Exception as e:
                    logger.error(f"Batch broadcast error: {e}")
                    failed_broadcasts += 1

        except Exception as e:
            logger.error(f"TaskGroup error during batch broadcast: {e}")
            failed_broadcasts = len(connection_ids)

        broadcast_time = time.time() - start_time
        if broadcast_time > self._batch_broadcast_warning_threshold:
            logger.warning(
                f"Slow batch broadcast to execution {execution_id}: "
                f"{broadcast_time:.2f}s for {len(messages)} events to {len(connection_ids)} connections "
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

    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event by routing it to subscribed connections.

        This method implements the EventHandler protocol, allowing the router
        to be subscribed directly to the DomainEventBus. It converts the event
        to a JSON-serializable format and broadcasts it to all connections
        subscribed to the execution.

        Additionally, it transforms certain domain events into UI-friendly events
        that the frontend expects.

        Args:
            event: The domain event to route
        """
        # Early return if no active connections - avoid processing during CLI operations
        if not self.execution_subscriptions and not self.local_handlers:
            return

        payload = event_to_json_payload(event)

        if event.scope.execution_id:
            await self.broadcast_to_execution(str(event.scope.execution_id), payload)

            if event.type in [
                EventType.NODE_STARTED,
                EventType.NODE_COMPLETED,
                EventType.NODE_ERROR,
            ]:
                node_status = (
                    "RUNNING"
                    if event.type == EventType.NODE_STARTED
                    else "COMPLETED"
                    if event.type == EventType.NODE_COMPLETED
                    else "FAILED"
                )
                ui_payload = {
                    "type": event.type.value,
                    "event_type": event.type.value,
                    "execution_id": str(event.scope.execution_id),
                    "data": {
                        "node_id": event.scope.node_id,
                        "status": node_status,
                        "timestamp": event.occurred_at.isoformat(),
                    },
                    "timestamp": event.occurred_at.isoformat(),
                }
                await self.broadcast_to_execution(str(event.scope.execution_id), ui_payload)

        else:
            logger.debug(f"Received global event: {event.type.value}")

    def _cleanup_old_buffers(self) -> None:
        """Clean up old event buffers based on TTL."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self._buffer_ttl_seconds)

        executions_to_remove = []

        # Clean up event buffers
        for execution_id, events in self._event_buffer.items():
            events[:] = [
                e
                for e in events
                if "timestamp" in e and datetime.fromisoformat(e["timestamp"]) > cutoff_time
            ]

            if not events:
                executions_to_remove.append(execution_id)

        # Remove empty executions from buffers
        for execution_id in executions_to_remove:
            self._event_buffer.pop(execution_id, None)

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
            "active_connections": len(self.local_handlers),
            "active_executions": len(self.execution_subscriptions),
            "total_subscriptions": sum(
                len(conns) for conns in self.execution_subscriptions.values()
            ),
            "unhealthy_connections": len(unhealthy_connections),
            "avg_queue_size": round(avg_queue_size, 2),
            "buffer_stats": {
                "total_executions": len(self._event_buffer),
                "buffer_sizes": {
                    exec_id: len(events) for exec_id, events in self._event_buffer.items()
                },
            },
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
