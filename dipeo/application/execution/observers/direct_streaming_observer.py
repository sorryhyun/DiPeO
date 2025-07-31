"""Direct streaming observer for CLI executions using Server-Sent Events."""

import asyncio
import json
from datetime import datetime
from typing import AsyncIterator, Dict, Any, Optional, Set
from collections import defaultdict

from dipeo.core.ports import ExecutionObserver
from dipeo.models import (
    ExecutionStatus,
    NodeExecutionStatus,
    NodeState,
    EventType,
)

try:
    from .scoped_observer import ObserverMetadata
except ImportError:
    from dipeo.application.execution.observers import ObserverMetadata


class DirectStreamingObserver(ExecutionObserver):
    """Observer that streams updates directly without message router.
    
    This observer is designed for CLI executions where the browser
    connects directly to an SSE endpoint to receive real-time updates.
    """
    
    def __init__(self, propagate_to_sub: bool = True, scope_to_parent: bool = False, execution_runtime=None):
        self.execution_runtime = execution_runtime
        # Store event queues for each execution
        self._event_queues: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()
        
        # Configure metadata for sub-diagram propagation
        self.metadata = ObserverMetadata(
            propagate_to_sub=propagate_to_sub,
            scope_to_execution=scope_to_parent,
            filter_events=None  # Stream all events by default
        )
    
    async def subscribe(self, execution_id: str) -> AsyncIterator[str]:
        """Subscribe to execution updates and yield SSE-formatted events."""
        queue: asyncio.Queue[Optional[dict]] = asyncio.Queue()
        
        async with self._lock:
            self._event_queues[execution_id].add(queue)
        
        try:
            while True:
                # Wait for event with timeout to allow periodic heartbeats
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if event is None:  # Sentinel value to close stream
                        break
                    
                    # Format as SSE
                    yield f"data: {json.dumps(event)}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield ": heartbeat\n\n"
                    
        finally:
            async with self._lock:
                self._event_queues[execution_id].discard(queue)
                if not self._event_queues[execution_id]:
                    del self._event_queues[execution_id]
    
    async def _publish(self, execution_id: str, event: dict):
        """Publish event to all subscribers."""
        async with self._lock:
            queues = list(self._event_queues.get(execution_id, []))
        
        # Publish to all queues
        for queue in queues:
            try:
                await queue.put(event)
            except asyncio.QueueFull:
                # Handle backpressure by dropping old events
                try:
                    queue.get_nowait()
                    await queue.put(event)
                except:
                    pass
    
    async def close_execution(self, execution_id: str):
        """Close all streams for an execution."""
        async with self._lock:
            queues = list(self._event_queues.get(execution_id, []))
        
        # Send sentinel value to close streams
        for queue in queues:
            try:
                await queue.put(None)
            except:
                pass
    
    async def on_execution_start(self, execution_id: str, diagram_id: str | None):
        await self._publish(
            execution_id,
            {
                "type": EventType.EXECUTION_STATUS_CHANGED.value,
                "execution_id": execution_id,
                "data": {
                    "status": ExecutionStatus.RUNNING.value,
                    "diagram_id": diagram_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )
    
    async def on_node_start(self, execution_id: str, node_id: str):
        # Get node type if runtime is available
        node_type = None
        if self.execution_runtime:
            from dipeo.models import NodeID
            node = self.execution_runtime.get_node(NodeID(node_id))
            if node:
                node_type = node.type.value if hasattr(node.type, 'value') else str(node.type)
        
        await self._publish(
            execution_id,
            {
                "type": EventType.NODE_STATUS_CHANGED.value,
                "execution_id": execution_id,
                "data": {
                    "node_id": node_id,
                    "status": NodeExecutionStatus.RUNNING.value,
                    "node_type": node_type,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )
    
    async def on_node_complete(self, execution_id: str, node_id: str, state: NodeState):
        # Get node type if runtime is available
        node_type = None
        if self.execution_runtime:
            from dipeo.models import NodeID
            node = self.execution_runtime.get_node(NodeID(node_id))
            if node:
                node_type = node.type.value if hasattr(node.type, 'value') else str(node.type)
        
        await self._publish(
            execution_id,
            {
                "type": EventType.NODE_STATUS_CHANGED.value,
                "execution_id": execution_id,
                "data": {
                    "node_id": node_id,
                    "status": state.status.value,
                    "node_type": node_type,
                    "output": state.output if state.output else None,
                    "started_at": state.started_at,
                    "ended_at": state.ended_at,
                    "token_usage": state.token_usage.model_dump() if state.token_usage else None,
                    "tokens_used": state.token_usage.total if state.token_usage else None,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )
    
    async def on_node_error(self, execution_id: str, node_id: str, error: str):
        # Get node type if runtime is available
        node_type = None
        if self.execution_runtime:
            from dipeo.models import NodeID
            node = self.execution_runtime.get_node(NodeID(node_id))
            if node:
                node_type = node.type.value if hasattr(node.type, 'value') else str(node.type)
        
        await self._publish(
            execution_id,
            {
                "type": EventType.NODE_STATUS_CHANGED.value,
                "execution_id": execution_id,
                "data": {
                    "node_id": node_id,
                    "status": NodeExecutionStatus.FAILED.value,
                    "node_type": node_type,
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )
    
    async def on_execution_complete(self, execution_id: str):
        await self._publish(
            execution_id,
            {
                "type": EventType.EXECUTION_STATUS_CHANGED.value,
                "execution_id": execution_id,
                "data": {
                    "status": ExecutionStatus.COMPLETED.value,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )
        # Close the stream after completion
        await self.close_execution(execution_id)
    
    async def on_execution_error(self, execution_id: str, error: str):
        await self._publish(
            execution_id,
            {
                "type": EventType.EXECUTION_ERROR.value,
                "execution_id": execution_id,
                "data": {
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )
        # Close the stream after error
        await self.close_execution(execution_id)