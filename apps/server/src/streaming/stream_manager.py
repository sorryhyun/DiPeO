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
    """Unified streaming for both SSE and WebSocket."""
    
    def __init__(self):
        self.active_streams: Dict[str, StreamContext] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.execution_subscriptions: Dict[str, Set[str]] = {}  # execution_id -> client_ids
        self._lock = asyncio.Lock()
        
    async def create_stream(
        self, 
        execution_id: str,
        output_format: Literal['sse', 'websocket', 'both']
    ) -> StreamContext:
        """Create a new stream context."""
        async with self._lock:
            context = StreamContext(execution_id, output_format)
            self.active_streams[execution_id] = context
            return context
    
    async def publish_update(self, execution_id: str, update: dict):
        """Publish to all subscribers of this execution."""
        async with self._lock:
            context = self.active_streams.get(execution_id)
            
        if context:
            await context.publish(update)
            
            # Handle WebSocket publishing
            if context.output_format in ('websocket', 'both'):
                await self._broadcast_to_websockets(execution_id, update)
    
    async def _broadcast_to_websockets(self, execution_id: str, update: dict):
        """Broadcast update to WebSocket subscribers."""
        subscribers = self.execution_subscriptions.get(execution_id, set()).copy()
        
        # Send outside the lock to avoid blocking
        for client_id in subscribers:
            if client_id in self.websocket_connections:
                try:
                    await self.websocket_connections[client_id].send_json(update)
                except Exception:
                    await self.disconnect_websocket(client_id)
    
    async def connect_websocket(self, websocket: WebSocket, client_id: str):
        """Connect a WebSocket client."""
        async with self._lock:
            await websocket.accept()
            self.websocket_connections[client_id] = websocket
    
    async def disconnect_websocket(self, client_id: str):
        """Disconnect a WebSocket client."""
        async with self._lock:
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]
            
            # Clean up subscriptions
            for exec_id in list(self.execution_subscriptions.keys()):
                if client_id in self.execution_subscriptions[exec_id]:
                    self.execution_subscriptions[exec_id].remove(client_id)
                    if not self.execution_subscriptions[exec_id]:
                        del self.execution_subscriptions[exec_id]
    
    async def subscribe_to_execution(self, client_id: str, execution_id: str):
        """Subscribe a WebSocket client to execution updates."""
        async with self._lock:
            if execution_id not in self.execution_subscriptions:
                self.execution_subscriptions[execution_id] = set()
            self.execution_subscriptions[execution_id].add(client_id)
    
    async def cleanup_stream(self, execution_id: str):
        """Clean up resources for a completed stream."""
        async with self._lock:
            if execution_id in self.active_streams:
                del self.active_streams[execution_id]
            if execution_id in self.execution_subscriptions:
                del self.execution_subscriptions[execution_id]
    
    def get_stream_queue(self, execution_id: str) -> Optional[asyncio.Queue]:
        """Get the SSE queue for a stream."""
        context = self.active_streams.get(execution_id)
        return context.sse_queue if context else None


# Global stream manager instance
stream_manager = StreamManager()