"""Adapter to convert ExecutionObserver to EventConsumer for backward compatibility."""

import logging
from typing import TYPE_CHECKING

from dipeo.core.events import EventConsumer, EventType, ExecutionEvent
from dipeo.core.ports import ExecutionObserver
from dipeo.infrastructure.events import AsyncEventBus

if TYPE_CHECKING:
    from dipeo.models import NodeState

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
            if event.type == EventType.EXECUTION_STARTED:
                await self.observer.on_execution_start(
                    execution_id=event.execution_id,
                    diagram_id=event.data.get("diagram_id")
                )
            
            elif event.type == EventType.NODE_STARTED:
                node_id = event.data.get("node_id")
                if node_id:
                    await self.observer.on_node_start(
                        execution_id=event.execution_id,
                        node_id=node_id
                    )
            
            elif event.type == EventType.NODE_COMPLETED:
                # Extract node state from event data
                node_state = event.data.get("node_state")
                node_id = event.data.get("node_id")
                if node_state and node_id:
                    await self.observer.on_node_complete(
                        execution_id=event.execution_id,
                        node_id=node_id,
                        state=node_state
                    )
            
            elif event.type == EventType.NODE_FAILED:
                node_id = event.data.get("node_id")
                if node_id:
                    await self.observer.on_node_error(
                        execution_id=event.execution_id,
                        node_id=node_id,
                        error=event.data.get("error", "Unknown error")
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
    
    return event_bus