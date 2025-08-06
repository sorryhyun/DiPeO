"""Async state manager that processes state updates via events."""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any

from dipeo.core.events import EventConsumer, EventType, ExecutionEvent
from dipeo.core.ports import StateStorePort
from dipeo.models import ExecutionStatus, NodeExecutionStatus
from .execution_state_cache import ExecutionStateCache

logger = logging.getLogger(__name__)


class AsyncStateManager(EventConsumer):
    """Processes execution events asynchronously to update state."""
    
    def __init__(self, state_store: StateStorePort, write_interval: float = 0.1):
        self.state_store = state_store
        self._write_buffer: dict[str, dict[str, Any]] = {}
        self._write_interval = write_interval
        self._write_task: asyncio.Task | None = None
        self._running = False
        self._buffer_lock = asyncio.Lock()
        self._execution_cache = ExecutionStateCache(ttl_seconds=3600)  # 1 hour TTL
    
    async def start(self) -> None:
        """Start the async state manager."""
        if self._running:
            return
            
        self._running = True
        await self._execution_cache.start()
        self._write_task = asyncio.create_task(self._write_loop())
        logger.info("AsyncStateManager started")
    
    async def stop(self) -> None:
        """Stop the async state manager and flush remaining writes."""
        self._running = False
        
        # Cancel write task
        if self._write_task:
            self._write_task.cancel()
            try:
                await self._write_task
            except asyncio.CancelledError:
                pass
        
        # Flush any remaining writes
        await self._flush_buffer()
        
        # Stop execution cache
        await self._execution_cache.stop()
        
        logger.info("AsyncStateManager stopped")
    
    async def consume(self, event: ExecutionEvent) -> None:
        """Process events asynchronously."""
        execution_id = event.execution_id
        
        # Buffer the event for batched writes
        async with self._buffer_lock:
            if execution_id not in self._write_buffer:
                self._write_buffer[execution_id] = {
                    "events": [],
                    "last_update": time.time()
                }
            
            self._write_buffer[execution_id]["events"].append(event)
            self._write_buffer[execution_id]["last_update"] = time.time()

    
    async def _write_loop(self) -> None:
        """Batch write to persistent storage."""
        while self._running:
            try:
                await asyncio.sleep(self._write_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                logger.info("Write loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in write loop: {e}", exc_info=True)
    
    async def _flush_buffer(self) -> None:
        """Flush buffered events to storage."""
        async with self._buffer_lock:
            if not self._write_buffer:
                return
            
            # Process all buffered executions
            for execution_id, buffer in list(self._write_buffer.items()):
                if buffer["events"]:
                    try:
                        await self._persist_events(execution_id, buffer["events"])
                        buffer["events"].clear()
                    except Exception as e:
                        logger.error(
                            f"Failed to persist events for execution {execution_id}: {e}",
                            exc_info=True
                        )
            
            # Clean up empty buffers
            self._write_buffer = {
                exec_id: buffer 
                for exec_id, buffer in self._write_buffer.items() 
                if buffer["events"]
            }
    
    async def _persist_events(
        self, execution_id: str, events: list[ExecutionEvent]
    ) -> None:
        """Persist a batch of events for an execution."""
        # Group events by type for efficient processing
        events_by_type = defaultdict(list)
        for event in events:
            events_by_type[event.type].append(event)
        
        # Process execution lifecycle events
        if EventType.EXECUTION_STARTED in events_by_type:
            await self._handle_execution_started(execution_id, events_by_type[EventType.EXECUTION_STARTED][-1])
        
        # Process node events
        for event in events_by_type.get(EventType.NODE_STARTED, []):
            await self._handle_node_started(execution_id, event)
        
        for event in events_by_type.get(EventType.NODE_COMPLETED, []):
            await self._handle_node_completed(execution_id, event)
        
        for event in events_by_type.get(EventType.NODE_FAILED, []):
            await self._handle_node_failed(execution_id, event)
        
        # Process metrics collection
        if EventType.METRICS_COLLECTED in events_by_type:
            await self._handle_metrics_collected(execution_id, events_by_type[EventType.METRICS_COLLECTED][-1])
        
        # Process execution completion
        if EventType.EXECUTION_COMPLETED in events_by_type:
            await self._handle_execution_completed(execution_id, events_by_type[EventType.EXECUTION_COMPLETED][-1])
    
    async def _handle_execution_started(
        self, execution_id: str, event: ExecutionEvent
    ) -> None:
        """Handle execution started event."""
        data = event.data
        diagram_id = data.get("diagram_id")
        variables = data.get("variables", {})
        
        # Create execution in cache first for fast access
        cache = await self._execution_cache.get_cache(execution_id)
        
        # Create execution in state store
        state = await self.state_store.create_execution(
            execution_id=execution_id,
            diagram_id=diagram_id,
            variables=variables
        )
        
        # Cache the initial state
        await cache.set_state(state)
        
        # Update status to running
        await self.state_store.update_status(
            execution_id=execution_id,
            status=ExecutionStatus.RUNNING
        )
    
    async def _handle_node_started(
        self, execution_id: str, event: ExecutionEvent
    ) -> None:
        """Handle node started event."""
        node_id = event.data.get("node_id")
        if not node_id:
            return
        
        await self.state_store.update_node_status(
            execution_id=execution_id,
            node_id=node_id,
            status=NodeExecutionStatus.RUNNING
        )
    
    async def _handle_node_completed(
        self, execution_id: str, event: ExecutionEvent
    ) -> None:
        """Handle node completed event."""
        data = event.data
        node_id = data.get("node_id")
        if not node_id:
            return
        
        # Update cache immediately for fast access
        cache = await self._execution_cache.get_cache(execution_id)
        
        # Update node output
        output = data.get("output")
        if output is not None:
            await cache.set_node_output(node_id, output)
            
            token_usage = data.get("metrics", {}).get("token_usage")
            await self.state_store.update_node_output(
                execution_id=execution_id,
                node_id=node_id,
                output=output,
                token_usage=token_usage
            )
        
        # Update node status in cache
        await cache.set_node_status(node_id, NodeExecutionStatus.COMPLETED)
        
        # Update node status in store
        await self.state_store.update_node_status(
            execution_id=execution_id,
            node_id=node_id,
            status=NodeExecutionStatus.COMPLETED
        )
    
    async def _handle_node_failed(
        self, execution_id: str, event: ExecutionEvent
    ) -> None:
        """Handle node failed event."""
        data = event.data
        node_id = data.get("node_id")
        if not node_id:
            return
        
        error = data.get("error", "Unknown error")
        
        # Update node status with error
        await self.state_store.update_node_status(
            execution_id=execution_id,
            node_id=node_id,
            status=NodeExecutionStatus.FAILED,
            error=error
        )
        
        # Store error as output
        await self.state_store.update_node_output(
            execution_id=execution_id,
            node_id=node_id,
            output={"error": error},
            is_exception=True
        )
    
    async def _handle_metrics_collected(
        self, execution_id: str, event: ExecutionEvent
    ) -> None:
        """Handle metrics collected event."""
        data = event.data
        metrics = data.get("metrics")
        
        if metrics:
            # Update execution metrics in state store
            await self.state_store.update_metrics(
                execution_id=execution_id,
                metrics=metrics
            )
            logger.debug(f"Saved metrics for execution {execution_id}")
    
    async def _handle_execution_completed(
        self, execution_id: str, event: ExecutionEvent
    ) -> None:
        """Handle execution completed event."""
        data = event.data
        status = data.get("status", ExecutionStatus.COMPLETED)
        error = data.get("error")
        
        # Update execution status
        await self.state_store.update_status(
            execution_id=execution_id,
            status=status,
            error=error
        )
        
        # Get the state from cache and persist it
        state = await self.state_store.get_state(execution_id)
        if state:
            await self.state_store.persist_final_state(state)
        
        # Remove from cache after persistence
        await self._execution_cache.remove_cache(execution_id)