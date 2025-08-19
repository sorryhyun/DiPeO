"""Adapter that converts domain events to ExecutionObserver calls."""

import logging
from typing import Any

from dipeo.application.execution.observer_protocol import ExecutionObserver
from dipeo.domain.events import DomainEvent, EventType

logger = logging.getLogger(__name__)


class EventToObserverAdapter:
    """Adapter that converts domain events to ExecutionObserver calls.
    
    This adapter allows event-based systems to notify traditional observers.
    It implements the EventHandler protocol expected by the event bus.
    """
    
    def __init__(self, observer: ExecutionObserver):
        """Initialize the adapter.
        
        Args:
            observer: The ExecutionObserver to notify
        """
        self._observer = observer
    
    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event by converting it to observer calls.
        
        Args:
            event: The domain event to handle
        """
        try:
            # Map event types to observer methods
            if event.type == EventType.EXECUTION_STARTED:
                await self._observer.on_execution_start(
                    execution_id=str(event.scope.execution_id),
                    diagram_id=event.payload.diagram_id if hasattr(event.payload, 'diagram_id') else None
                )
                
            elif event.type == EventType.NODE_STARTED:
                await self._observer.on_node_start(
                    execution_id=str(event.scope.execution_id),
                    node_id=str(event.scope.node_id) if event.scope.node_id else ""
                )
                
            elif event.type == EventType.NODE_COMPLETED:
                # Get state from payload if available
                state = event.payload.state if hasattr(event.payload, 'state') else None
                await self._observer.on_node_complete(
                    execution_id=str(event.scope.execution_id),
                    node_id=str(event.scope.node_id) if event.scope.node_id else "",
                    state=state
                )
                
            elif event.type == EventType.NODE_ERROR:
                error_msg = event.payload.error_message if hasattr(event.payload, 'error_message') else "Unknown error"
                await self._observer.on_node_error(
                    execution_id=str(event.scope.execution_id),
                    node_id=str(event.scope.node_id) if event.scope.node_id else "",
                    error=error_msg
                )
                
            elif event.type == EventType.EXECUTION_COMPLETED:
                status = event.payload.status if hasattr(event.payload, 'status') else None
                if status and str(status).upper() == "FAILED":
                    error_msg = event.payload.error_message if hasattr(event.payload, 'error_message') else "Execution failed"
                    await self._observer.on_execution_error(
                        execution_id=str(event.scope.execution_id),
                        error=error_msg
                    )
                else:
                    await self._observer.on_execution_complete(
                        execution_id=str(event.scope.execution_id)
                    )
                    
            # Ignore other event types that don't map to observer methods
            else:
                logger.debug(f"Ignoring event type {event.type} - no observer mapping")
                
        except Exception as e:
            logger.error(f"Error converting event to observer call: {e}")
            # Don't re-raise to avoid breaking the event processing chain