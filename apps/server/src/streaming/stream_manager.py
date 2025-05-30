import asyncio
from datetime import datetime
from typing import Dict, Set, Literal, Optional
from fastapi import WebSocket


class StreamContext:
    """Context for a single stream execution."""
    
    def __init__(self, execution_id: str, output_format: Literal['sse', 'websocket', 'both']):
        self.execution_id = execution_id
        self.output_format = output_format
        self.sse_queue: Optional[asyncio.Queue] = None
        self.websocket_clients: Set[str] = set()
        self.created_at = datetime.now()
        
        if output_format in ('sse', 'both'):
            self.sse_queue = asyncio.Queue(maxsize=1000)
    
    async def publish(self, update: dict):
        """Publish update to all subscribers."""
        if self.sse_queue and self.output_format in ('sse', 'both'):
            try:
                self.sse_queue.put_nowait(update)
            except asyncio.QueueFull:
                # Drop oldest update to prevent memory leak
                try:
                    await asyncio.wait_for(self.sse_queue.get(), timeout=0.01)
                    self.sse_queue.put_nowait(update)
                except (asyncio.TimeoutError, asyncio.QueueFull):
                    pass
        
        # WebSocket publishing will be handled by StreamManager
        if self.output_format in ('websocket', 'both'):
            # This will be called by StreamManager
            pass


class StreamManager:
    """Unified streaming for SSE only."""

    def __init__(self):
        self.active_streams: Dict[str, StreamContext] = {}
        self.monitor_queues: Dict[str, asyncio.Queue] = {}  # Add monitor queues
        self._lock = asyncio.Lock()

    async def create_stream(
            self,
            execution_id: str,
            output_format: Literal['sse'] = 'sse'  # SSE only
    ) -> StreamContext:
        """Create a new stream context."""
        async with self._lock:
            context = StreamContext(execution_id, output_format)
            self.active_streams[execution_id] = context
            return context

    async def add_monitor(self, monitor_id: str) -> asyncio.Queue:
        """Add a monitoring client and return its queue."""
        async with self._lock:
            queue = asyncio.Queue(maxsize=100)
            self.monitor_queues[monitor_id] = queue
            return queue

    async def remove_monitor(self, monitor_id: str):
        """Remove a monitoring client."""
        async with self._lock:
            if monitor_id in self.monitor_queues:
                del self.monitor_queues[monitor_id]

    async def publish_update(self, execution_id: str, update: dict):
        """Publish to all subscribers of this execution."""
        async with self._lock:
            context = self.active_streams.get(execution_id)

        if context:
            await context.publish(update)

        # Broadcast to all monitors
        await self._broadcast_to_monitors(execution_id, update)

    async def _broadcast_to_monitors(self, execution_id: str, update: dict):
        """Broadcast update to all SSE monitors."""
        # Get monitor list without holding lock
        async with self._lock:
            monitor_items = list(self.monitor_queues.items())

        # Broadcast outside lock
        for monitor_id, queue in monitor_items:
            try:
                # Add execution_id to update
                monitor_update = {
                    **update,
                    'execution_id': execution_id,
                    'from_monitor': True
                }
                queue.put_nowait(monitor_update)
            except asyncio.QueueFull:
                # Skip if queue is full
                pass

    # Remove all WebSocket methods
    # Remove: connect_websocket, disconnect_websocket, subscribe_to_execution, _broadcast_to_websockets

    async def cleanup_stream(self, execution_id: str):
        """Clean up resources for a completed stream."""
        async with self._lock:
            if execution_id in self.active_streams:
                del self.active_streams[execution_id]


# Global stream manager instance
stream_manager = StreamManager()