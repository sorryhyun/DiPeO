"""SSE adapter for MessageRouter to provide unified real-time monitoring."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime

from dipeo.core.ports import MessageRouterPort

logger = logging.getLogger(__name__)


class SSEMessageRouterAdapter:
    """Adapter that bridges MessageRouter to Server-Sent Events.

    This adapter allows SSE endpoints to consume events from the central
    MessageRouter, unifying real-time monitoring across CLI and Web clients.
    """

    def __init__(self, message_router: MessageRouterPort):
        self.message_router = message_router
        self._active_streams: dict[str, int] = {}

    async def subscribe(self, execution_id: str) -> AsyncIterator[dict]:
        """Subscribe to execution updates via MessageRouter and yield SSE events.

        Args:
            execution_id: The execution to monitor

        Yields:
            SSE-formatted event dictionaries with 'data' field
        """
        # Create unique connection ID for this SSE stream
        connection_id = f"sse-{execution_id}-{id(self)}"
        event_queue: asyncio.Queue[dict | None] = asyncio.Queue(maxsize=100)

        # Handler that puts MessageRouter events into our queue
        async def sse_handler(message: dict):
            try:
                # Don't block if queue is full (apply backpressure)
                await asyncio.wait_for(event_queue.put(message), timeout=0.1)
            except (TimeoutError, asyncio.QueueFull):
                # Drop event if client can't keep up
                logger.warning(f"SSE queue full for {execution_id}, dropping event")

        try:
            # Register with MessageRouter
            await self.message_router.register_connection(connection_id, sse_handler)
            await self.message_router.subscribe_connection_to_execution(connection_id, execution_id)

            # Track active stream
            self._active_streams[execution_id] = self._active_streams.get(execution_id, 0) + 1

            # Send initial connection event
            yield {
                "data": json.dumps(
                    {
                        "type": "CONNECTION_ESTABLISHED",
                        "execution_id": execution_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            }

            # Main event loop
            while True:
                try:
                    # Wait for event with timeout for heartbeats
                    event = await asyncio.wait_for(event_queue.get(), timeout=10.0)

                    if event is None:  # Sentinel to close stream
                        break

                    # Yield as SSE data event
                    yield {"data": json.dumps(event)}

                except TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield {
                        "data": json.dumps(
                            {
                                "type": "HEARTBEAT",
                                "execution_id": execution_id,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                    }

        finally:
            # Cleanup
            await self.message_router.unsubscribe_connection_from_execution(
                connection_id, execution_id
            )
            await self.message_router.unregister_connection(connection_id)

            # Update stream count
            self._active_streams[execution_id] = self._active_streams.get(execution_id, 1) - 1
            if self._active_streams[execution_id] <= 0:
                self._active_streams.pop(execution_id, None)

    def get_stats(self) -> dict:
        """Get adapter statistics."""
        return {
            "active_sse_streams": len(self._active_streams),
            "streams_by_execution": dict(self._active_streams),
        }
