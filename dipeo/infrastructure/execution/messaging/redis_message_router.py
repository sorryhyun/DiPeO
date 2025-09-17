"""Redis-backed message router for distributed event distribution.

This module provides a Redis-based message routing implementation that enables
GraphQL subscriptions to work across multiple worker processes.
"""

import asyncio
import contextlib
import json
import logging

import redis.asyncio as redis
from redis.asyncio.client import PubSub

from dipeo.config import get_settings
from dipeo.infrastructure.execution.messaging.base_message_router import BaseMessageRouter

logger = logging.getLogger(__name__)


class RedisMessageRouter(BaseMessageRouter):
    """Redis-backed message router for multi-worker GraphQL subscriptions.

    This router uses Redis Pub/Sub to distribute execution events across
    multiple worker processes, enabling GraphQL subscriptions to work properly
    when running with --workers > 1.

    Key features:
    - Cross-worker event distribution via Redis Pub/Sub
    - Maintains backward compatibility with MessageRouter interface
    - Local handler management per worker
    - Automatic Redis subscription management
    """

    def __init__(self):
        super().__init__()
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
        self._subscription_tasks: dict[str, asyncio.Task] = {}
        self._subscribed_executions: set[str] = set()
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
            # Cancel subscription tasks
            for task in self._subscription_tasks.values():
                if task and not task.done():
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task

            # Cancel batch tasks
            for task in self._batch_tasks.values():
                if task and not task.done():
                    task.cancel()

            # Flush remaining batches
            for execution_id in list(self._batch_queue.keys()):
                await self._flush_batch(execution_id)

            # Close Redis connection
            if self.redis_client:
                await self.redis_client.aclose()
                self.redis_client = None

            # Clear all data structures
            self.local_handlers.clear()
            self.execution_subscriptions.clear()
            self.connection_health.clear()
            self._subscription_tasks.clear()
            self._subscribed_executions.clear()
            self._batch_queue.clear()
            self._batch_tasks.clear()
            self._event_buffer.clear()
            self._message_queue_size.clear()

            self._initialized = False
            logger.info(f"RedisMessageRouter cleaned up for worker {self.worker_id}")

    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a connection and clean up its subscriptions.

        Extends the base implementation to also manage Redis subscriptions.

        Args:
            connection_id: Connection identifier to remove
        """
        # Call parent implementation
        await super().unregister_connection(connection_id)

        # Additionally, check if we need to unsubscribe from Redis
        for exec_id in list(self.execution_subscriptions.keys()):
            if exec_id not in self.execution_subscriptions:
                # If no more local connections for this execution, unsubscribe from Redis
                await self._unsubscribe_from_redis(exec_id)

        logger.debug(f"Unregistered connection {connection_id} from worker {self.worker_id}")

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast a message to all connections subscribed to an execution.

        This implementation publishes to Redis, which will distribute to all workers.

        Args:
            execution_id: Execution identifier
            message: Message to broadcast
        """
        if not self._initialized:
            await self.initialize()

        # Buffer event for late connections
        if self._should_buffer_events(execution_id):
            await self._buffer_event(execution_id, message)

        # Publish to Redis
        channel = f"exec:{execution_id}"
        try:
            message_json = json.dumps(message)
            await self.redis_client.publish(channel, message_json)
        except Exception as e:
            logger.error(f"Failed to publish to Redis channel {channel}: {e}")

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Subscribe a connection to receive updates for a specific execution.

        Extends the base implementation to also manage Redis subscriptions.

        Args:
            connection_id: Connection identifier
            execution_id: Execution to subscribe to
        """
        # Call parent implementation
        await super().subscribe_connection_to_execution(connection_id, execution_id)

        # Additionally, subscribe to Redis if not already subscribed
        if execution_id not in self._subscribed_executions:
            await self._subscribe_to_redis(execution_id)

        logger.debug(
            f"Connection {connection_id} subscribed to execution {execution_id} "
            f"on worker {self.worker_id}"
        )

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Unsubscribe a connection from an execution.

        Extends the base implementation to also manage Redis subscriptions.

        Args:
            connection_id: Connection identifier
            execution_id: Execution to unsubscribe from
        """
        # Call parent implementation
        await super().unsubscribe_connection_from_execution(connection_id, execution_id)

        # Additionally, unsubscribe from Redis if no more local connections
        if execution_id not in self.execution_subscriptions:
            await self._unsubscribe_from_redis(execution_id)

    async def _subscribe_to_redis(self, execution_id: str) -> None:
        """Subscribe to Redis channel for an execution.

        Args:
            execution_id: Execution to subscribe to
        """
        if execution_id in self._subscribed_executions:
            return

        self._subscribed_executions.add(execution_id)

        # Create subscription task
        task = asyncio.create_task(self._redis_subscription_handler(execution_id))
        self._subscription_tasks[execution_id] = task

        logger.debug(f"Started Redis subscription for execution {execution_id}")

    async def _unsubscribe_from_redis(self, execution_id: str) -> None:
        """Unsubscribe from Redis channel for an execution.

        Args:
            execution_id: Execution to unsubscribe from
        """
        if execution_id not in self._subscribed_executions:
            return

        self._subscribed_executions.discard(execution_id)

        # Cancel subscription task
        task = self._subscription_tasks.pop(execution_id, None)
        if task and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        logger.debug(f"Stopped Redis subscription for execution {execution_id}")

    async def _redis_subscription_handler(self, execution_id: str) -> None:
        """Handle Redis subscription for a specific execution.

        This coroutine subscribes to a Redis channel and processes incoming
        messages by batching them and routing to local connections.

        Args:
            execution_id: Execution to handle subscription for
        """
        channel = f"exec:{execution_id}"

        # Create dedicated Redis client for subscription
        sub_client = redis.from_url(self.redis_url, decode_responses=True)
        pubsub = sub_client.pubsub()

        try:
            await pubsub.subscribe(channel)
            logger.debug(f"Subscribed to Redis channel {channel}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])

                        # Only process if we have local connections
                        if execution_id in self.execution_subscriptions:
                            # Add to batch queue
                            if execution_id not in self._batch_queue:
                                self._batch_queue[execution_id] = []

                            self._batch_queue[execution_id].append(data)

                            # Flush if batch is full or schedule delayed flush
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

    def get_stats(self) -> dict:
        """Get router statistics and health metrics.

        Returns:
            Dictionary containing router stats and connection health
        """
        # Get base stats
        stats = super().get_stats()

        # Add RedisMessageRouter-specific stats
        stats["worker_id"] = self.worker_id
        stats["redis_subscriptions"] = len(self._subscribed_executions)

        return stats
