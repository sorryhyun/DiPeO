"""Streaming monitor service for real-time UI updates without performance impact."""

import asyncio
import logging
from typing import Any

from dipeo.core.events import EventConsumer, EventType, ExecutionEvent
from dipeo.core.ports import MessageRouterPort

logger = logging.getLogger(__name__)


class StreamingMonitor(EventConsumer):
    """Processes events for real-time UI updates without impacting execution performance.
    
    This service:
    - Consumes execution events asynchronously
    - Transforms events to UI-friendly format
    - Forwards events to GraphQL subscriptions via MessageRouter
    - Provides backpressure to prevent memory issues
    """
    
    def __init__(self, message_router: MessageRouterPort, queue_size: int = 10000):
        self.message_router = message_router
        self._event_queue = asyncio.Queue(maxsize=queue_size)  # Bounded queue for backpressure
        self._running = False
        self._process_task: asyncio.Task | None = None
    
    async def start(self) -> None:
        """Start the streaming monitor."""
        if self._running:
            return
        
        self._running = True
        self._process_task = asyncio.create_task(self._process_events())
    
    async def stop(self) -> None:
        """Stop the streaming monitor."""
        self._running = False
        
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
    
    async def consume(self, event: ExecutionEvent) -> None:
        """Consume events asynchronously without blocking execution."""
        # Critical events should be processed immediately
        if event.type == EventType.EXECUTION_COMPLETED:
            # Process critical events immediately without queueing
            await self._handle_event(event)
            return
        
        try:
            # Non-blocking put to avoid impacting execution
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(
                f"Event queue full, dropping event for execution {event.execution_id}"
            )
    
    async def _process_events(self) -> None:
        """Process events from the queue and forward to clients."""
        while self._running:
            try:
                # Wait for events with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(), timeout=1.0
                )
                
                # Transform and forward event
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.debug("Event processing cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
    
    async def _handle_event(self, event: ExecutionEvent) -> None:
        """Handle a single event."""
        # Transform event for UI
        ui_event = self._transform_for_ui(event)
        
        # Send through message router (which handles all subscriptions)
        await self.message_router.broadcast_to_execution(
            execution_id=event.execution_id,
            message=ui_event
        )
    
    def _transform_for_ui(self, event: ExecutionEvent) -> dict[str, Any]:
        """Convert internal events to UI-friendly format."""
        base_event = {
            "type": event.type.value,
            "executionId": event.execution_id,
            "timestamp": event.timestamp,
        }
        
        # Add type-specific fields
        if event.type == EventType.EXECUTION_STARTED:
            return {
                **base_event,
                "event_type": "EXECUTION_STATUS_CHANGED",
                "data": {
                    "status": "STARTED",
                    "diagramId": event.data.get("diagram_id"),
                    "diagramName": event.data.get("diagram_name"),
                }
            }
        
        elif event.type == EventType.NODE_STARTED:
            return {
                **base_event,
                "event_type": "NODE_STATUS_CHANGED",
                "data": {
                    "node_id": event.data.get("node_id"),
                    "status": "RUNNING",
                    "node_type": event.data.get("node_type"),
                }
            }
        
        elif event.type == EventType.NODE_COMPLETED:
            return {
                **base_event,
                "event_type": "NODE_STATUS_CHANGED",
                "data": {
                    "node_id": event.data.get("node_id"),
                    "status": "COMPLETED",
                    "output": self._sanitize_output(event.data.get("output")),
                    "metrics": event.data.get("metrics", {}),
                }
            }
        
        elif event.type == EventType.NODE_FAILED:
            return {
                **base_event,
                "event_type": "NODE_STATUS_CHANGED",
                "data": {
                    "node_id": event.data.get("node_id"),
                    "status": "FAILED",
                    "error": event.data.get("error"),
                }
            }
        
        elif event.type == EventType.EXECUTION_COMPLETED:
            return {
                **base_event,
                "event_type": "EXECUTION_STATUS_CHANGED",
                "data": {
                    "status": self._map_completion_status(event.data.get("status")),
                    "error": event.data.get("error"),
                    "summary": event.data.get("summary", {}),
                }
            }
        
        elif event.type == EventType.METRICS_COLLECTED:
            return {
                **base_event,
                "metrics": event.data.get("metrics", {}),
            }
        
        else:
            # Unknown event type, pass through
            return {
                **base_event,
                "data": event.data,
            }
    
    @staticmethod
    def _sanitize_output(output: Any) -> Any:
        """Sanitize output for UI display."""
        if output is None:
            return None
        
        # For large outputs, truncate or summarize
        if isinstance(output, str) and len(output) > 1000:
            return output[:1000] + "... (truncated)"
        
        # For complex objects, extract key information
        if isinstance(output, dict):
            # Handle protocol outputs
            if "_protocol_type" in output:
                return {
                    "type": output.get("_protocol_type"),
                    "value": output.get("value"),
                    "metadata": output.get("metadata", {}),
                }
            
            # Limit dict size
            if len(str(output)) > 1000:
                return {"_summary": "Large output truncated", "keys": list(output.keys())}
        
        return output
    
    @staticmethod
    def _map_completion_status(status: Any) -> str:
        """Map internal status to UI status."""
        if status is None:
            return "COMPLETED"
        
        # Check if it's a Status enum
        from dipeo.diagram_generated import Status
        if isinstance(status, Status):
            return status.value  # This returns the uppercase string like 'COMPLETED', 'FAILED', etc.
        
        status_str = str(status).upper()
        if "COMPLETED" in status_str or "MAXITER" in status_str:
            return "COMPLETED"
        elif "FAILED" in status_str:
            return "FAILED"
        elif "ABORT" in status_str:
            return "ABORTED"
        else:
            return status_str
    
    @staticmethod
    def _map_status(event_type: EventType) -> str:
        """Map event type to UI status."""
        if event_type == EventType.EXECUTION_STARTED:
            return "started"
        elif event_type == EventType.NODE_STARTED:
            return "running"
        elif event_type == EventType.NODE_COMPLETED:
            return "completed"
        elif event_type == EventType.NODE_FAILED:
            return "failed"
        elif event_type == EventType.EXECUTION_COMPLETED:
            return "completed"
        else:
            return "unknown"