"""Message router implementation for real-time event distribution.

This module provides the central message routing infrastructure that distributes
execution events to GraphQL subscriptions.
"""

import asyncio
import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from dipeo.config import get_settings
from dipeo.domain.events.contracts import DomainEvent
from dipeo.domain.events.unified_ports import EventBus as MessageRouterPort
from dipeo.domain.events.unified_ports import EventHandler
from dipeo.infrastructure.events.serialize import event_to_json_payload

logger = logging.getLogger(__name__)


@dataclass
class ConnectionHealth:
    last_successful_send: float
    failed_attempts: int = 0
    total_messages: int = 0
    avg_latency: float = 0.0


class MessageRouter(MessageRouterPort, EventHandler[DomainEvent]):
    """Central message router implementing the MessageRouterPort protocol and EventHandler.

    This router manages connections and routes execution events to GraphQL
    subscriptions. It serves as the single source of truth for real-time monitoring.

    As an EventHandler, it subscribes to the DomainEventBus and forwards events
    to GraphQL connections, eliminating the need for separate adapters.

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
        settings = get_settings()
        self.max_queue_size = settings.messaging.max_queue_size
        self._event_buffer: dict[str, list[dict]] = {}
        self._buffer_max_size = settings.messaging.buffer_max_per_exec
        self._buffer_ttl_seconds = settings.messaging.buffer_ttl_s
        self._sequence_counters: dict[str, int] = {}
        self._replay_buffers: dict[str, deque] = {}  # Ring buffers for replay
        self._batch_queue: dict[str, list[dict]] = {}
        self._batch_tasks: dict[str, asyncio.Task | None] = {}
        self._batch_broadcast_warning_threshold = settings.messaging.broadcast_warning_threshold_s
        self._batch_interval = settings.messaging.batch_interval_ms / 1000.0
        self._batch_max_size = settings.messaging.batch_max

    async def initialize(self) -> None:
        if self._initialized:
            return

        self._initialized = True

    async def cleanup(self) -> None:
        for task in self._batch_tasks.values():
            if task and not task.done():
                task.cancel()

        for execution_id in list(self._batch_queue.keys()):
            await self._flush_batch(execution_id)

        self.local_handlers.clear()
        self.execution_subscriptions.clear()
        self.connection_health.clear()
        self._message_queue_size.clear()
        self._batch_queue.clear()
        self._batch_tasks.clear()
        self._sequence_counters.clear()
        self._replay_buffers.clear()
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

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast a message to all connections subscribed to an execution.

        Args:
            execution_id: Execution identifier
            message: Message to broadcast
        """
        # Add sequence ID
        seq = self._get_next_sequence(execution_id)
        message["seq"] = seq

        # Store in replay buffer
        if self._should_buffer_events(execution_id):
            self._add_to_replay_buffer(execution_id, message)

        connection_ids = self.execution_subscriptions.get(execution_id, set())
        if not connection_ids and not self._should_buffer_events(execution_id):
            return

        if self._should_buffer_events(execution_id):
            await self._buffer_event(execution_id, message)

        if not connection_ids:
            return

        if execution_id not in self._batch_queue:
            self._batch_queue[execution_id] = []

        self._batch_queue[execution_id].append(message)

        if len(self._batch_queue[execution_id]) >= self._batch_max_size:
            await self._flush_batch(execution_id)
        else:
            if execution_id not in self._batch_tasks or self._batch_tasks[execution_id] is None:
                self._batch_tasks[execution_id] = asyncio.create_task(
                    self._delayed_flush(execution_id)
                )

    async def _delayed_flush(self, execution_id: str) -> None:
        await asyncio.sleep(self._batch_interval)
        await self._flush_batch(execution_id)

    async def _flush_batch(self, execution_id: str) -> None:
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
        else:
            pass

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

        await self._replay_buffered_events(connection_id, execution_id)

    async def subscribe_with_replay(
        self, connection_id: str, execution_id: str, last_seq: int | None = None
    ) -> None:
        """Subscribe a connection to an execution with replay capability.

        Args:
            connection_id: Connection identifier
            execution_id: Execution to subscribe to
            last_seq: Last sequence number client received. If provided, replays missed messages.
        """
        # Subscribe to live updates
        if execution_id not in self.execution_subscriptions:
            self.execution_subscriptions[execution_id] = set()

        self.execution_subscriptions[execution_id].add(connection_id)

        # Replay missed messages if requested
        if last_seq is not None:
            missed_messages = self._get_messages_since(execution_id, last_seq)
            for msg in missed_messages:
                success = await self.route_to_connection(connection_id, msg)
                if not success:
                    logger.warning(
                        f"Failed to replay message seq={msg.get('seq')} to connection {connection_id}"
                    )
                    break

            logger.info(
                f"Replayed {len(missed_messages)} messages to connection {connection_id} "
                f"for execution {execution_id} since seq={last_seq}"
            )
        else:
            # Fallback to legacy buffer replay if no sequence specified
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

    def _get_next_sequence(self, execution_id: str) -> int:
        """Get the next sequence number for an execution.

        Args:
            execution_id: Execution identifier

        Returns:
            Next sequence number for this execution
        """
        if execution_id not in self._sequence_counters:
            self._sequence_counters[execution_id] = 0
        self._sequence_counters[execution_id] += 1
        return self._sequence_counters[execution_id]

    def _add_to_replay_buffer(self, execution_id: str, message: dict) -> None:
        """Add a message to the replay buffer with sequence ID.

        Args:
            execution_id: Execution identifier
            message: Message to buffer (should already have seq field)
        """
        if execution_id not in self._replay_buffers:
            # Create ring buffer with max size
            self._replay_buffers[execution_id] = deque(maxlen=self._buffer_max_size)

        self._replay_buffers[execution_id].append(message.copy())

    def _get_messages_since(self, execution_id: str, last_seq: int) -> list[dict]:
        """Get all messages since a given sequence number.

        Args:
            execution_id: Execution identifier
            last_seq: Last sequence number client received

        Returns:
            List of messages with seq > last_seq
        """
        if execution_id not in self._replay_buffers:
            return []

        replay_buffer = self._replay_buffers[execution_id]
        missed_messages = []

        for message in replay_buffer:
            message_seq = message.get("seq", 0)
            if message_seq > last_seq:
                missed_messages.append(message)

        return missed_messages

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
                logger.warning(
                    f"[MessageRouter] Failed to replay event to connection {connection_id}"
                )
                break

    def _cleanup_old_buffers(self) -> None:
        """Clean up old event buffers and replay buffers based on TTL."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self._buffer_ttl_seconds)

        executions_to_remove = []

        # Clean up legacy event buffers
        for execution_id, events in self._event_buffer.items():
            events[:] = [
                e
                for e in events
                if "timestamp" in e and datetime.fromisoformat(e["timestamp"]) > cutoff_time
            ]

            if not events:
                executions_to_remove.append(execution_id)

        # Clean up replay buffers (sequence-based)
        for execution_id, replay_buffer in list(self._replay_buffers.items()):
            # Filter messages in replay buffer by timestamp
            filtered_messages = []
            for message in replay_buffer:
                if "timestamp" in message:
                    try:
                        msg_time = datetime.fromisoformat(message["timestamp"])
                        if msg_time > cutoff_time:
                            filtered_messages.append(message)
                    except (ValueError, TypeError):
                        # Keep message if timestamp is invalid (safer than dropping)
                        filtered_messages.append(message)
                else:
                    # Keep message if no timestamp (safer than dropping)
                    filtered_messages.append(message)

            # Replace the deque contents
            if filtered_messages:
                self._replay_buffers[execution_id] = deque(
                    filtered_messages, maxlen=self._buffer_max_size
                )
            else:
                executions_to_remove.append(execution_id)

        # Remove empty executions from all buffers and counters
        for execution_id in executions_to_remove:
            self._event_buffer.pop(execution_id, None)
            self._replay_buffers.pop(execution_id, None)
            self._sequence_counters.pop(execution_id, None)

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

        # Calculate replay buffer statistics
        replay_buffer_sizes = {
            exec_id: len(buffer) for exec_id, buffer in self._replay_buffers.items()
        }
        avg_replay_buffer_size = (
            sum(replay_buffer_sizes.values()) / len(replay_buffer_sizes)
            if replay_buffer_sizes
            else 0
        )

        # Calculate sequence statistics
        max_sequence = max(self._sequence_counters.values()) if self._sequence_counters else 0
        total_messages_with_seq = sum(self._sequence_counters.values())

        return {
            "worker_id": self.worker_id,
            "active_connections": len(self.local_handlers),
            "active_executions": len(self.execution_subscriptions),
            "total_subscriptions": sum(
                len(conns) for conns in self.execution_subscriptions.values()
            ),
            "unhealthy_connections": len(unhealthy_connections),
            "avg_queue_size": round(avg_queue_size, 2),
            # New replay and sequence metrics
            "replay_buffers": {
                "total_executions": len(self._replay_buffers),
                "buffer_sizes": replay_buffer_sizes,
                "avg_buffer_size": round(avg_replay_buffer_size, 2),
                "max_buffer_size": max(replay_buffer_sizes.values()) if replay_buffer_sizes else 0,
            },
            "sequence_tracking": {
                "total_executions": len(self._sequence_counters),
                "max_sequence": max_sequence,
                "total_messages_sent": total_messages_with_seq,
            },
            # Legacy event buffer metrics for comparison
            "legacy_buffers": {
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

    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event by routing it to subscribed connections.

        This method implements the EventHandler protocol, allowing the router
        to be subscribed directly to the DomainEventBus. It converts the event
        to a JSON-serializable format and broadcasts it to all connections
        subscribed to the execution.

        Additionally, it transforms certain domain events into UI-friendly events
        that the frontend expects (replacing the removed StreamingMonitor functionality).

        Args:
            event: The domain event to route
        """
        payload = event_to_json_payload(event)

        if event.scope.execution_id:
            await self.broadcast_to_execution(str(event.scope.execution_id), payload)
            from dipeo.domain.events import EventType

            if event.type == EventType.EXECUTION_STARTED:
                ui_payload = {
                    "type": "EXECUTION_STATUS_CHANGED",
                    "event_type": "EXECUTION_STATUS_CHANGED",
                    "execution_id": str(event.scope.execution_id),
                    "data": {"status": "RUNNING", "timestamp": event.occurred_at.isoformat()},
                    "timestamp": event.occurred_at.isoformat(),
                }
                await self.broadcast_to_execution(str(event.scope.execution_id), ui_payload)

            elif event.type == EventType.EXECUTION_COMPLETED:
                if hasattr(event.payload, "status"):
                    status = event.payload.status
                elif isinstance(event.payload, dict):
                    status = event.payload.get("status", "COMPLETED")
                else:
                    status = "COMPLETED"

                ui_payload = {
                    "type": "EXECUTION_STATUS_CHANGED",
                    "event_type": "EXECUTION_STATUS_CHANGED",
                    "execution_id": str(event.scope.execution_id),
                    "data": {
                        "status": status,
                        "is_final": True,
                        "timestamp": event.occurred_at.isoformat(),
                    },
                    "timestamp": event.occurred_at.isoformat(),
                }
                await self.broadcast_to_execution(str(event.scope.execution_id), ui_payload)

            elif event.type == EventType.NODE_STATUS_CHANGED:
                ui_payload = {
                    "type": "NODE_STATUS_CHANGED",
                    "event_type": "NODE_STATUS_CHANGED",
                    "execution_id": str(event.scope.execution_id),
                    "data": {
                        "node_id": event.scope.node_id,
                        "status": event.meta.get("status") if event.meta else "UNKNOWN",
                        "timestamp": event.occurred_at.isoformat(),
                    },
                    "timestamp": event.occurred_at.isoformat(),
                }
                await self.broadcast_to_execution(str(event.scope.execution_id), ui_payload)

            elif event.type in [
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
                    "type": "NODE_STATUS_CHANGED",
                    "event_type": "NODE_STATUS_CHANGED",
                    "execution_id": str(event.scope.execution_id),
                    "data": {
                        "node_id": event.scope.node_id,
                        "status": node_status,
                        "timestamp": event.occurred_at.isoformat(),
                    },
                    "timestamp": event.occurred_at.isoformat(),
                }
                await self.broadcast_to_execution(str(event.scope.execution_id), ui_payload)

            elif event.type == EventType.METRICS_COLLECTED:
                ui_payload = {
                    "type": "METRICS_COLLECTED",
                    "event_type": "METRICS_COLLECTED",
                    "execution_id": str(event.scope.execution_id),
                    "data": payload.get("data", payload),
                    "timestamp": event.occurred_at.isoformat(),
                }
                await self.broadcast_to_execution(str(event.scope.execution_id), ui_payload)
        else:
            logger.debug(f"Received global event: {event.type.value}")


message_router = MessageRouter()
