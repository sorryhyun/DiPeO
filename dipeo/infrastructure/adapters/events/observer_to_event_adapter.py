"""Adapter that converts ExecutionObserver calls to domain events."""

import logging
from datetime import datetime
from typing import Optional

from dipeo.application.migration.compat_imports import ExecutionObserver
from dipeo.diagram_generated import NodeState
from dipeo.domain.events import (
    DomainEventBus,
    ExecutionStartedEvent,
    ExecutionCompletedEvent,
    ExecutionErrorEvent,
    NodeStartedEvent,
    NodeCompletedEvent,
    NodeErrorEvent,
)

logger = logging.getLogger(__name__)


class ObserverToEventAdapter(ExecutionObserver):
    """Adapter that converts ExecutionObserver calls to domain events.
    
    This adapter allows existing code using the observer pattern
    to emit domain events without modification.
    """
    
    def __init__(
        self,
        event_bus: DomainEventBus,
        correlation_id: Optional[str] = None
    ):
        """Initialize the adapter.
        
        Args:
            event_bus: Domain event bus to publish events to
            correlation_id: Optional correlation ID for all events
        """
        self._event_bus = event_bus
        self._correlation_id = correlation_id
    
    async def on_execution_start(
        self,
        execution_id: str,
        diagram_id: str | None
    ) -> None:
        """Convert execution start to domain event."""
        event = ExecutionStartedEvent(
            execution_id=execution_id,
            diagram_id=diagram_id,
            correlation_id=self._correlation_id,
        )
        await self._event_bus.publish(event)
        logger.debug(f"Published ExecutionStartedEvent for {execution_id}")
    
    async def on_node_start(self, execution_id: str, node_id: str) -> None:
        """Convert node start to domain event."""
        event = NodeStartedEvent(
            execution_id=execution_id,
            node_id=node_id,
            correlation_id=self._correlation_id,
        )
        await self._event_bus.publish(event)
        logger.debug(f"Published NodeStartedEvent for {node_id}")
    
    async def on_node_complete(
        self,
        execution_id: str,
        node_id: str,
        state: NodeState
    ) -> None:
        """Convert node completion to domain event."""
        # Calculate duration if timestamps available
        duration_ms = None
        if state.started_at and state.ended_at:
            duration = (state.ended_at - state.started_at).total_seconds()
            duration_ms = int(duration * 1000)
        
        # Extract token usage if available
        token_usage = None
        if state.token_usage:
            token_usage = state.token_usage.model_dump()
        
        event = NodeCompletedEvent(
            execution_id=execution_id,
            node_id=node_id,
            state=state,
            duration_ms=duration_ms,
            token_usage=token_usage,
            correlation_id=self._correlation_id,
        )
        await self._event_bus.publish(event)
        logger.debug(f"Published NodeCompletedEvent for {node_id}")
    
    async def on_node_error(
        self,
        execution_id: str,
        node_id: str,
        error: str
    ) -> None:
        """Convert node error to domain event."""
        event = NodeErrorEvent(
            execution_id=execution_id,
            node_id=node_id,
            error=error,
            correlation_id=self._correlation_id,
        )
        await self._event_bus.publish(event)
        logger.debug(f"Published NodeErrorEvent for {node_id}")
    
    async def on_execution_complete(self, execution_id: str) -> None:
        """Convert execution completion to domain event."""
        from dipeo.diagram_generated import Status
        
        event = ExecutionCompletedEvent(
            execution_id=execution_id,
            status=Status.COMPLETED,
            correlation_id=self._correlation_id,
        )
        await self._event_bus.publish(event)
        logger.debug(f"Published ExecutionCompletedEvent for {execution_id}")
    
    async def on_execution_error(
        self,
        execution_id: str,
        error: str
    ) -> None:
        """Convert execution error to domain event."""
        event = ExecutionErrorEvent(
            execution_id=execution_id,
            error=error,
            correlation_id=self._correlation_id,
        )
        await self._event_bus.publish(event)
        logger.debug(f"Published ExecutionErrorEvent for {execution_id}")