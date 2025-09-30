"""In-memory message router implementation for single-process deployments.

This module provides the in-memory message routing implementation that distributes
execution events directly to local GraphQL subscriptions.
"""

import asyncio
import logging

from dipeo.config.base_logger import get_module_logger
import threading
from collections import deque

from dipeo.infrastructure.execution.messaging.base_message_router import BaseMessageRouter

logger = get_module_logger(__name__)

class MessageRouter(BaseMessageRouter):
    """In-memory message router for single-process deployments.

    This router manages connections and routes execution events directly to
    local GraphQL subscriptions without external dependencies. It extends
    the base router with sequence tracking and replay capabilities.
    """

    def __init__(self):
        super().__init__()
        self.worker_id = "single-worker"
        self._queue_lock = threading.Lock()

        # Sequence tracking for replay
        self._sequence_counters: dict[str, int] = {}
        self._replay_buffers: dict[str, deque] = {}  # Ring buffers for replay

    async def initialize(self) -> None:
        """Initialize the router."""
        if self._initialized:
            return

        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up router resources."""
        # Cancel batch tasks
        for task in self._batch_tasks.values():
            if task and not task.done():
                task.cancel()

        # Flush remaining batches
        for execution_id in list(self._batch_queue.keys()):
            await self._flush_batch(execution_id)

        # Clear all data structures
        self.local_handlers.clear()
        self.execution_subscriptions.clear()
        self.connection_health.clear()
        self._message_queue_size.clear()
        self._batch_queue.clear()
        self._batch_tasks.clear()
        self._sequence_counters.clear()
        self._replay_buffers.clear()
        self._event_buffer.clear()
        self._initialized = False
        logger.info("MessageRouter cleaned up")

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast a message to all connections subscribed to an execution.

        This implementation directly routes to local connections with sequence
        tracking and replay buffering.

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

        # Buffer event for late connections
        if self._should_buffer_events(execution_id):
            await self._buffer_event(execution_id, message)

        if not connection_ids:
            return

        # Add to batch queue
        if execution_id not in self._batch_queue:
            self._batch_queue[execution_id] = []

        self._batch_queue[execution_id].append(message)

        # Flush if batch is full or schedule delayed flush
        if len(self._batch_queue[execution_id]) >= self._batch_max_size:
            await self._flush_batch(execution_id)
        else:
            if execution_id not in self._batch_tasks or self._batch_tasks[execution_id] is None:
                self._batch_tasks[execution_id] = asyncio.create_task(
                    self._delayed_flush(execution_id)
                )

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

    def _cleanup_old_buffers(self) -> None:
        """Clean up old event buffers and replay buffers based on TTL."""
        # Call parent cleanup
        super()._cleanup_old_buffers()

        # Clean up replay buffers
        from datetime import datetime, timedelta

        cutoff_time = datetime.utcnow() - timedelta(seconds=self._buffer_ttl_seconds)
        executions_to_remove = []

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

        # Remove empty executions
        for execution_id in executions_to_remove:
            self._replay_buffers.pop(execution_id, None)
            self._sequence_counters.pop(execution_id, None)

    def get_stats(self) -> dict:
        """Get router statistics and health metrics.

        Returns:
            Dictionary containing router stats and connection health
        """
        # Get base stats
        stats = super().get_stats()

        # Add MessageRouter-specific stats
        stats["worker_id"] = self.worker_id

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

        stats["replay_buffers"] = {
            "total_executions": len(self._replay_buffers),
            "buffer_sizes": replay_buffer_sizes,
            "avg_buffer_size": round(avg_replay_buffer_size, 2),
            "max_buffer_size": max(replay_buffer_sizes.values()) if replay_buffer_sizes else 0,
        }

        stats["sequence_tracking"] = {
            "total_executions": len(self._sequence_counters),
            "max_sequence": max_sequence,
            "total_messages_sent": total_messages_with_seq,
        }

        return stats

# Singleton instance for backward compatibility
message_router = MessageRouter()
