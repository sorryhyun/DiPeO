"""Redis-backed message router for distributed event distribution.

This module provides a Redis-based message routing implementation that enables
GraphQL subscriptions to work across multiple worker processes.
"""

import asyncio
import contextlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import redis.asyncio as redis
from redis.asyncio.client import PubSub

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


class RedisMessageRouter(MessageRouterPort, EventHandler[DomainEvent]):
    """Redis-backed message router for multi-worker GraphQL subscriptions.

    This router uses Redis Pub/Sub to distribute execution events across
    multiple worker processes, enabling GraphQL subscriptions to work properly
    when running with --workers > 1.

    Key features:
    - Cross-worker event distribution via Redis Pub/Sub
    - Maintains backward compatibility with MessageRouter interface
    - Local handler management per worker
    - Health monitoring and automatic cleanup
    - Event buffering for late connections
    """

    def __init__(self):
        settings = get_settings()
        self.redis_url = settings.messaging.redis_url
        if not self.redis_url:
            import os

            self.redis_url = os.getenv("DIPEO_REDIS_URL")
            if not self.redis_url:
                raise ValueError(
                    "Redis URL not configured. Set DIPEO_REDIS_URL environment variable."
                )

        self.redis_client: redis.Redis | None = None
        self.pubsub_client: PubSub | None = None
        self.worker_id = f"worker-{id(self)}"
        self.local_handlers: dict[str, Callable] = {}
        self.execution_subscriptions: dict[str, set[str]] = {}
        self.connection_health: dict[str, ConnectionHealth] = {}
        self._subscription_tasks: dict[str, asyncio.Task] = {}
        self._subscribed_executions: set[str] = set()

        self.max_queue_size = settings.messaging.max_queue_size
        self._buffer_max_size = settings.messaging.buffer_max_per_exec
        self._buffer_ttl_seconds = settings.messaging.buffer_ttl_s
        self._batch_interval = settings.messaging.batch_interval_ms / 1000.0
        self._batch_max_size = settings.messaging.batch_max
        self._batch_broadcast_warning_threshold = settings.messaging.broadcast_warning_threshold_s
        self._event_buffer: dict[str, list[dict]] = {}
        self._batch_queue: dict[str, list[dict]] = {}
        self._batch_tasks: dict[str, asyncio.Task | None] = {}

        self._initialized = False
        self._cleanup_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize Redis connections."""
        if self._initialized:
            return

        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()

            self._initialized = True
            logger.info(f"RedisMessageRouter initialized for worker {self.worker_id}")

        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up Redis connections and subscriptions."""
        async with self._cleanup_lock:
            for task in self._subscription_tasks.values():
                if task and not task.done():
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task

            for task in self._batch_tasks.values():
                if task and not task.done():
                    task.cancel()

            for execution_id in list(self._batch_queue.keys()):
                await self._flush_batch(execution_id)

            if self.redis_client:
                await self.redis_client.aclose()
                self.redis_client = None

            self.local_handlers.clear()
            self.execution_subscriptions.clear()
            self.connection_health.clear()
            self._subscription_tasks.clear()
            self._subscribed_executions.clear()
            self._batch_queue.clear()
            self._batch_tasks.clear()
            self._event_buffer.clear()

            self._initialized = False
            logger.info(f"RedisMessageRouter cleaned up for worker {self.worker_id}")

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        """Register a new WebSocket connection with its message handler."""
        self.local_handlers[connection_id] = handler
        self.connection_health[connection_id] = ConnectionHealth(last_successful_send=time.time())
        logger.debug(f"Registered connection {connection_id} on worker {self.worker_id}")

    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a connection and clean up its subscriptions."""
        self.local_handlers.pop(connection_id, None)
        self.connection_health.pop(connection_id, None)

        for exec_id, connections in list(self.execution_subscriptions.items()):
            connections.discard(connection_id)
            if not connections:
                del self.execution_subscriptions[exec_id]
                await self._unsubscribe_from_redis(exec_id)

        logger.debug(f"Unregistered connection {connection_id} from worker {self.worker_id}")

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Subscribe a connection to receive updates for a specific execution."""
        if execution_id not in self.execution_subscriptions:
            self.execution_subscriptions[execution_id] = set()

        self.execution_subscriptions[execution_id].add(connection_id)

        if execution_id not in self._subscribed_executions:
            await self._subscribe_to_redis(execution_id)

        await self._replay_buffered_events(connection_id, execution_id)

        logger.debug(
            f"Connection {connection_id} subscribed to execution {execution_id} "
            f"on worker {self.worker_id}"
        )

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Unsubscribe a connection from an execution."""
        if execution_id in self.execution_subscriptions:
            self.execution_subscriptions[execution_id].discard(connection_id)

            if not self.execution_subscriptions[execution_id]:
                del self.execution_subscriptions[execution_id]
                await self._unsubscribe_from_redis(execution_id)

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast a message to all connections subscribed to an execution.

        This publishes to Redis, which will distribute to all workers.
        """
        if not self._initialized:
            await self.initialize()

        if self._should_buffer_events(execution_id):
            await self._buffer_event(execution_id, message)
        channel = f"exec:{execution_id}"
        try:
            message_json = json.dumps(message)
            await self.redis_client.publish(channel, message_json)
            logger.debug(f"Published message to Redis channel {channel}")
        except Exception as e:
            logger.error(f"Failed to publish to Redis channel {channel}: {e}")

    async def route_to_connection(self, connection_id: str, message: dict) -> bool:
        """Route a message to a specific local connection."""
        handler = self.local_handlers.get(connection_id)
        if not handler:
            return False

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

    async def _subscribe_to_redis(self, execution_id: str) -> None:
        """Subscribe to Redis channel for an execution."""
        if execution_id in self._subscribed_executions:
            return

        self._subscribed_executions.add(execution_id)

        task = asyncio.create_task(self._redis_subscription_handler(execution_id))
        self._subscription_tasks[execution_id] = task

        logger.debug(f"Started Redis subscription for execution {execution_id}")

    async def _unsubscribe_from_redis(self, execution_id: str) -> None:
        """Unsubscribe from Redis channel for an execution."""
        if execution_id not in self._subscribed_executions:
            return

        self._subscribed_executions.discard(execution_id)

        task = self._subscription_tasks.pop(execution_id, None)
        if task and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        logger.debug(f"Stopped Redis subscription for execution {execution_id}")

    async def _redis_subscription_handler(self, execution_id: str) -> None:
        """Handle Redis subscription for a specific execution."""
        channel = f"exec:{execution_id}"

        sub_client = redis.from_url(self.redis_url, decode_responses=True)
        pubsub = sub_client.pubsub()

        try:
            await pubsub.subscribe(channel)
            logger.debug(f"Subscribed to Redis channel {channel}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])

                        if execution_id in self.execution_subscriptions:
                            if execution_id not in self._batch_queue:
                                self._batch_queue[execution_id] = []

                            self._batch_queue[execution_id].append(data)

                            if len(self._batch_queue[execution_id]) >= self._batch_max_size:
                                await self._flush_batch(execution_id)
                            else:
                                if (
                                    execution_id not in self._batch_tasks
                                    or self._batch_tasks[execution_id] is None
                                ):
                                    self._batch_tasks[execution_id] = asyncio.create_task(
                                        self._delayed_flush(execution_id)
                                    )

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode Redis message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")

        except asyncio.CancelledError:
            logger.debug(f"Redis subscription cancelled for {channel}")
            raise
        except Exception as e:
            logger.error(f"Redis subscription error for {channel}: {e}")
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            await sub_client.aclose()

    async def _delayed_flush(self, execution_id: str) -> None:
        """Flush batch after a delay."""
        await asyncio.sleep(self._batch_interval)
        await self._flush_batch(execution_id)

    async def _flush_batch(self, execution_id: str) -> None:
        """Flush batched messages to local connections."""
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

            async def track_broadcast(conn_id: str, msg: dict):
                result = await self.route_to_connection(conn_id, msg)
                return conn_id, result

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

    def _should_buffer_events(self, execution_id: str) -> bool:
        """Check if events should be buffered for an execution."""
        return "_batch_" not in execution_id

    async def _buffer_event(self, execution_id: str, message: dict) -> None:
        """Buffer an event for late connections."""
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
        """Replay buffered events to a new connection."""
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

    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event by publishing it to Redis.

        This implements the EventHandler protocol, allowing the router
        to be subscribed directly to the DomainEventBus.
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
        else:
            logger.debug(f"Received global event: {event.type.value}")

    def get_stats(self) -> dict:
        """Get router statistics and health metrics."""
        now = time.time()
        unhealthy_connections = [
            conn_id
            for conn_id, health in self.connection_health.items()
            if now - health.last_successful_send > 60
        ]

        return {
            "worker_id": self.worker_id,
            "active_connections": len(self.local_handlers),
            "active_executions": len(self.execution_subscriptions),
            "redis_subscriptions": len(self._subscribed_executions),
            "total_subscriptions": sum(
                len(conns) for conns in self.execution_subscriptions.values()
            ),
            "unhealthy_connections": len(unhealthy_connections),
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
