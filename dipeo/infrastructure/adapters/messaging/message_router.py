"""Message router implementation for real-time event distribution.

This module provides the central message routing infrastructure that distributes
execution events to GraphQL subscriptions.
"""

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

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

    This router manages connections and routes execution events to GraphQL
    subscriptions. It serves as the single source of truth for real-time monitoring.

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
        
        # Event buffering for late connections
        self._event_buffer: dict[str, list[dict]] = {}
        self._buffer_max_size = 50  # Keep last 50 events per execution
        self._buffer_ttl_seconds = 300  # Keep events for 5 minutes
        
        # Event batching for performance
        self._batch_queue: dict[str, list[dict]] = {}
        self._batch_tasks: dict[str, asyncio.Task | None] = {}
        self._batch_interval = 0.05  # 50ms batching window
        self._batch_max_size = 20  # Max events per batch

    async def initialize(self) -> None:
        """Initialize the message router."""
        if self._initialized:
            return

        self._initialized = True
        logger.info("MessageRouter initialized")

    async def cleanup(self) -> None:
        """Clean up all connections and subscriptions."""
        # Cancel all pending batch tasks
        for task in self._batch_tasks.values():
            if task and not task.done():
                task.cancel()
        
        # Flush any remaining batches
        for execution_id in list(self._batch_queue.keys()):
            await self._flush_batch(execution_id)
        
        self.local_handlers.clear()
        self.execution_subscriptions.clear()
        self.connection_health.clear()
        self._message_queue_size.clear()
        self._batch_queue.clear()
        self._batch_tasks.clear()
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

        # Remove from all execution subscriptions
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
        # Quick exit if no connections and no need to buffer
        connection_ids = self.execution_subscriptions.get(execution_id, set())
        if not connection_ids and not self._should_buffer_events(execution_id):
            return  # Skip all expensive operations
        
        # Buffer the event for late connections only if needed
        if self._should_buffer_events(execution_id):
            await self._buffer_event(execution_id, message)

        # If no active connections, skip broadcasting
        if not connection_ids:
            return

        # Add message to batch queue
        if execution_id not in self._batch_queue:
            self._batch_queue[execution_id] = []
        
        self._batch_queue[execution_id].append(message)
        
        # Check if we should flush immediately (batch full)
        if len(self._batch_queue[execution_id]) >= self._batch_max_size:
            await self._flush_batch(execution_id)
        else:
            # Schedule batch flush if not already scheduled
            if execution_id not in self._batch_tasks or self._batch_tasks[execution_id] is None:
                self._batch_tasks[execution_id] = asyncio.create_task(
                    self._delayed_flush(execution_id)
                )

    async def _delayed_flush(self, execution_id: str) -> None:
        """Flush batch after a delay."""
        await asyncio.sleep(self._batch_interval)
        await self._flush_batch(execution_id)
    
    async def _flush_batch(self, execution_id: str) -> None:
        """Flush all batched messages for an execution."""
        # Get and clear the batch
        messages = self._batch_queue.pop(execution_id, [])
        if execution_id in self._batch_tasks:
            self._batch_tasks[execution_id] = None
        
        if not messages:
            return
        
        connection_ids = self.execution_subscriptions.get(execution_id, set())
        if not connection_ids:
            return
        
        start_time = time.time()
        
        # Create a batch message containing all events
        batch_message = {
            "type": "BATCH_UPDATE",
            "execution_id": execution_id,
            "events": messages,
            "timestamp": datetime.utcnow().isoformat(),
            "batch_size": len(messages)
        }
        
        # Try to publish to GraphQL subscriptions (if available)
        try:
            from dipeo_server.api.graphql.subscriptions import publish_execution_update
            await publish_execution_update(execution_id, batch_message)
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Failed to publish batch to streaming manager: {e}")
        
        successful_broadcasts = 0
        failed_broadcasts = 0
        
        # Broadcast batch to all connections
        import sys
        if sys.version_info >= (3, 11):
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
        else:
            tasks = []
            for conn_id in list(connection_ids):
                tasks.append(self._broadcast_with_metrics(conn_id, batch_message))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Failed to broadcast batch to connection: {result}")
                        failed_broadcasts += 1
                    elif result:
                        successful_broadcasts += 1

        # Log performance
        broadcast_time = time.time() - start_time
        if broadcast_time > 0.1:
            logger.warning(
                f"Slow batch broadcast to execution {execution_id}: "
                f"{broadcast_time:.2f}s for {len(messages)} events to {len(connection_ids)} connections "
                f"(success: {successful_broadcasts}, failed: {failed_broadcasts})"
            )
        else:
            logger.debug(
                f"Batch broadcast to {execution_id}: {len(messages)} events in {broadcast_time:.3f}s"
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
        # logger.debug(f"[MessageRouter] Subscribing connection {connection_id} to execution {execution_id}")
        
        if execution_id not in self.execution_subscriptions:
            self.execution_subscriptions[execution_id] = set()

        self.execution_subscriptions[execution_id].add(connection_id)
        # logger.debug(f"[MessageRouter] Connection subscribed successfully, total subs for {execution_id}: {len(self.execution_subscriptions[execution_id])}")
        
        # Replay buffered events to the new connection
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

            # Clean up empty subscription sets
            if not self.execution_subscriptions[execution_id]:
                del self.execution_subscriptions[execution_id]


    def _should_buffer_events(self, execution_id: str) -> bool:
        """Check if events should be buffered for an execution.
        
        Skip buffering for batch item executions to save memory.
        """
        # Don't buffer for batch item executions (they have _batch_ in the ID)
        if "_batch_" in execution_id:
            return False
        
        # Buffer for normal executions
        return True
    
    async def _buffer_event(self, execution_id: str, message: dict) -> None:
        """Buffer an event for late connections.
        
        Args:
            execution_id: Execution identifier
            message: Event message to buffer
        """
        # Initialize buffer if needed
        if execution_id not in self._event_buffer:
            self._event_buffer[execution_id] = []
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        # Add to buffer
        self._event_buffer[execution_id].append(message)
        
        # Trim buffer if it exceeds max size
        if len(self._event_buffer[execution_id]) > self._buffer_max_size:
            self._event_buffer[execution_id] = self._event_buffer[execution_id][-self._buffer_max_size:]

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
        

        # Send buffered events to the new connection
        for event in buffered_events:
            # Skip heartbeat and connection events
            event_type = event.get("type", "")
            if event_type in ["HEARTBEAT", "CONNECTION_ESTABLISHED"]:
                continue
                
            # Send the event to the specific connection
            success = await self.route_to_connection(connection_id, event)
            if not success:
                logger.warning(f"[MessageRouter] Failed to replay event to connection {connection_id}")
                break
        

    def _cleanup_old_buffers(self) -> None:
        """Clean up old event buffers based on TTL."""
        now = time.time()
        cutoff_time = datetime.utcnow() - timedelta(seconds=self._buffer_ttl_seconds)
        
        executions_to_remove = []
        for execution_id, events in self._event_buffer.items():
            # Remove old events
            events[:] = [
                e for e in events
                if "timestamp" in e and datetime.fromisoformat(e["timestamp"]) > cutoff_time
            ]
            
            # Mark empty buffers for removal
            if not events:
                executions_to_remove.append(execution_id)
        
        # Remove empty buffers
        for execution_id in executions_to_remove:
            del self._event_buffer[execution_id]

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
