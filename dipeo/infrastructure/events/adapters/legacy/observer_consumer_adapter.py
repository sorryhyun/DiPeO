"""Adapter to convert ExecutionObserver to EventConsumer for backward compatibility."""

import logging
from typing import TYPE_CHECKING

from dipeo.domain.events import EventConsumer, EventType, ExecutionEvent
from dipeo.application.execution.observer_protocol import ExecutionObserver
from dipeo.diagram_generated.enums import Status

from .async_event_bus import AsyncEventBus

if TYPE_CHECKING:
    from dipeo.diagram_generated import NodeState

logger = logging.getLogger(__name__)


class ObserverToEventConsumerAdapter(EventConsumer):
    """Adapts ExecutionObserver to work as an EventConsumer.
    
    This allows existing observers to work with the new event-based engine
    without modification.
    """
    
    def __init__(self, observer: ExecutionObserver):
        self.observer = observer
    
    async def consume(self, event: ExecutionEvent) -> None:
        """Convert events to observer method calls."""
        try:
            # Handle both old and new event formats
            event_type = getattr(event, 'event_type', getattr(event, 'type', None))
            event_data = getattr(event, 'data', {}) if hasattr(event, 'data') else {}
            
            if event_type == EventType.EXECUTION_STARTED:
                await self.observer.on_execution_start(
                    execution_id=event.execution_id,
                    diagram_id=event_data.get("diagram_id") or getattr(event, 'diagram_id', None)
                )
            
            elif event_type == EventType.NODE_STARTED:
                node_id = event_data.get("node_id") or getattr(event, 'node_id', None)
                # logger.debug(f"[ObserverAdapter] NODE_STARTED event received for node {node_id}")
                if node_id:
                    # logger.debug(f"[ObserverAdapter] Calling observer.on_node_start for node {node_id}")
                    await self.observer.on_node_start(
                        execution_id=event.execution_id,
                        node_id=node_id
                    )
            
            elif event_type == EventType.NODE_COMPLETED:
                # Extract node state from event data or direct attribute
                node_state = event_data.get("node_state") or event_data.get("state") or getattr(event, 'state', None)
                node_id = event_data.get("node_id") or getattr(event, 'node_id', None)
                if node_state and node_id:
                    await self.observer.on_node_complete(
                        execution_id=event.execution_id,
                        node_id=node_id,
                        state=node_state
                    )
            
            elif event_type == EventType.NODE_ERROR:
                node_id = event_data.get("node_id") or getattr(event, 'node_id', None)
                error = event_data.get("error") or getattr(event, 'error', "Unknown error")
                if node_id:
                    await self.observer.on_node_error(
                        execution_id=event.execution_id,
                        node_id=node_id,
                        error=error
                    )
            
            elif event_type == EventType.EXECUTION_COMPLETED:
                # Check if it's an error completion
                status = event_data.get("status") or getattr(event, 'status', None)
                if status == Status.FAILED:
                    error = event_data.get("error") or getattr(event, 'error', "Unknown error")
                    await self.observer.on_execution_error(
                        execution_id=event.execution_id,
                        error=error
                    )
                else:
                    await self.observer.on_execution_complete(
                        execution_id=event.execution_id
                    )
            
            # Other event types are ignored as they don't map to observer methods
            
        except Exception as e:
            logger.error(f"Error in observer adapter: {e}", exc_info=True)


def create_event_bus_with_observers(observers: list[ExecutionObserver]) -> AsyncEventBus:
    """Create an event bus with observer adapters pre-configured.
    
    This utility function creates an event bus and automatically subscribes
    observer adapters for all provided observers.
    """
    event_bus = AsyncEventBus()
    
    for observer in observers:
        adapter = ObserverToEventConsumerAdapter(observer)
        
        # Subscribe to all relevant event types
        event_bus.subscribe(EventType.EXECUTION_STARTED, adapter)
        event_bus.subscribe(EventType.NODE_STARTED, adapter)
        event_bus.subscribe(EventType.NODE_COMPLETED, adapter)
        event_bus.subscribe(EventType.NODE_FAILED, adapter)
        event_bus.subscribe(EventType.EXECUTION_COMPLETED, adapter)
    
    return event_bus