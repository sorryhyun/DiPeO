"""Unified event observer that publishes domain events to the event bus."""

import logging
from datetime import datetime

from dipeo.application.execution.observer_protocol import ExecutionObserver
from dipeo.domain.events.ports import DomainEventBus
from dipeo.domain.events import (
    DomainEvent,
    EventScope,
    ExecutionStartedPayload,
    ExecutionCompletedPayload,
    ExecutionErrorPayload,
    NodeStartedPayload,
    NodeCompletedPayload,
    NodeErrorPayload,
    ExecutionLogPayload,
    EventType,
)
from dipeo.diagram_generated import (
    Status,
    NodeState,
)

try:
    from .scoped_observer import ObserverMetadata
except ImportError:
    from dipeo.application.execution.observers import ObserverMetadata

logger = logging.getLogger(__name__)


class UnifiedEventObserver(ExecutionObserver):
    """Unified observer that publishes domain events to the event bus.

    This observer creates proper domain event objects and publishes them
    to the domain event bus, keeping all serialization and infrastructure
    concerns in the infrastructure layer.
    """

    def __init__(
        self, event_bus: DomainEventBus, execution_runtime=None, capture_logs: bool = True,
        propagate_to_sub: bool = False
    ):
        self.event_bus = event_bus
        self.execution_runtime = execution_runtime
        self.capture_logs = capture_logs
        self._log_handler: logging.Handler | None = None

        # Configure metadata for sub-diagram propagation
        self.metadata = ObserverMetadata(
            propagate_to_sub=propagate_to_sub,
            scope_to_execution=False,
            filter_events=None,  # Publish all events
        )

    async def on_execution_start(self, execution_id: str, diagram_id: str | None):
        """Handle execution start event."""
        # Set up log capture if enabled
        if self.capture_logs:
            self._setup_log_capture(execution_id)

        event = DomainEvent(
            type=EventType.EXECUTION_STARTED,
            scope=EventScope(execution_id=execution_id),
            payload=ExecutionStartedPayload(
                variables={},  # TODO: Get actual variables from context
                diagram_id=diagram_id,
            )
        )
        await self.event_bus.publish(event)

    async def on_node_start(self, execution_id: str, node_id: str):
        """Handle node start event."""
        node_type = self._get_node_type(node_id)
        
        # Create a minimal NodeState for the start event
        state = NodeState(
            status=Status.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        
        event = DomainEvent(
            type=EventType.NODE_STARTED,
            scope=EventScope(execution_id=execution_id, node_id=node_id),
            payload=NodeStartedPayload(
                state=state,
                node_type=node_type,
                inputs=None,  # TODO: Get actual inputs from context
            )
        )
        await self.event_bus.publish(event)

    async def on_node_complete(self, execution_id: str, node_id: str, state: NodeState):
        """Handle node completion event."""
        node_type = self._get_node_type(node_id)
        
        # Calculate duration if both timestamps are available
        duration_ms = None
        if state.started_at and state.ended_at:
            # Parse ISO format strings if they're strings
            started = datetime.fromisoformat(state.started_at) if isinstance(state.started_at, str) else state.started_at
            ended = datetime.fromisoformat(state.ended_at) if isinstance(state.ended_at, str) else state.ended_at
            duration_ms = int((ended - started).total_seconds() * 1000)
        
        event = DomainEvent(
            type=EventType.NODE_COMPLETED,
            scope=EventScope(execution_id=execution_id, node_id=node_id),
            payload=NodeCompletedPayload(
                state=state,
                output=state.output,
                duration_ms=duration_ms,
                token_usage=state.token_usage.model_dump() if state.token_usage else None,
                output_summary=str(state.output)[:100] if state.output else None,  # Brief summary
            )
        )
        await self.event_bus.publish(event)

    async def on_node_error(self, execution_id: str, node_id: str, error: str):
        """Handle node error event."""
        node_type = self._get_node_type(node_id)
        
        # Create error state
        state = NodeState(
            status=Status.FAILED,
            error=error,
            ended_at=datetime.now().isoformat(),
        )
        
        event = DomainEvent(
            type=EventType.NODE_ERROR,
            scope=EventScope(execution_id=execution_id, node_id=node_id),
            payload=NodeErrorPayload(
                state=state,
                error_message=error,
                error_type=type(error).__name__ if not isinstance(error, str) else "Error",
                retryable=False,  # TODO: Determine from error type
            )
        )
        await self.event_bus.publish(event)

    async def on_execution_complete(self, execution_id: str):
        """Handle execution completion event."""
        event = DomainEvent(
            type=EventType.EXECUTION_COMPLETED,
            scope=EventScope(execution_id=execution_id),
            payload=ExecutionCompletedPayload(
                status=Status.COMPLETED,
            )
        )
        await self.event_bus.publish(event)

        # Clean up log capture
        if self._log_handler:
            self._cleanup_log_capture()

    async def on_execution_error(self, execution_id: str, error: str):
        """Handle execution error event."""
        event = DomainEvent(
            type=EventType.EXECUTION_ERROR,
            scope=EventScope(execution_id=execution_id),
            payload=ExecutionErrorPayload(
                error_message=error,
                error_type=type(error).__name__ if not isinstance(error, str) else "Error",
            )
        )
        await self.event_bus.publish(event)

        # Clean up log capture
        if self._log_handler:
            self._cleanup_log_capture()

    async def _publish_log_event(self, execution_id: str, log_entry: dict):
        """Publish log event to event bus."""
        event = DomainEvent(
            type=EventType.EXECUTION_LOG,
            scope=EventScope(
                execution_id=execution_id,
                node_id=log_entry.get("node_id")
            ),
            payload=ExecutionLogPayload(
                level=log_entry["level"],
                message=log_entry["message"],
                logger_name=log_entry["logger"],
                extra_fields={
                    "timestamp": log_entry["timestamp"],
                },
            )
        )
        await self.event_bus.publish(event)

    def _get_node_type(self, node_id: str) -> str:
        """Get node type from runtime context if available."""
        if self.execution_runtime:
            # Access the execution runtime's node registry
            try:
                node = self.execution_runtime.get_node(node_id)
                if node:
                    return node.__class__.__name__
            except:
                pass
        return "Unknown"

    def _setup_log_capture(self, execution_id: str):
        """Set up log capture handler for the execution."""
        # TODO: Implement log capture setup
        pass

    def _cleanup_log_capture(self):
        """Clean up log capture handler."""
        # TODO: Implement log capture cleanup
        pass