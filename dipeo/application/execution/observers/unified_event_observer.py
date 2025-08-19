"""Unified event observer that publishes domain events to the event bus."""

import logging
from datetime import datetime

from dipeo.application.execution.observer_protocol import ExecutionObserver
from dipeo.domain.events.ports import DomainEventBus
from dipeo.domain.events.contracts import (
    ExecutionStartedEvent,
    ExecutionCompletedEvent,
    ExecutionErrorEvent,
    NodeStartedEvent,
    NodeCompletedEvent,
    NodeErrorEvent,
    ExecutionLogEvent,
)
from dipeo.diagram_generated import (
    EventType,
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

        event = ExecutionStartedEvent(
            execution_id=execution_id,
            diagram_id=diagram_id,
            variables={},  # TODO: Get actual variables from context
        )
        await self.event_bus.publish(event)

    async def on_node_start(self, execution_id: str, node_id: str):
        """Handle node start event."""
        node_type = self._get_node_type(node_id)
        
        event = NodeStartedEvent(
            execution_id=execution_id,
            node_id=node_id,
            node_type=node_type,
            inputs=None,  # TODO: Get actual inputs from context
        )
        await self.event_bus.publish(event)

    async def on_node_complete(self, execution_id: str, node_id: str, state: NodeState):
        """Handle node completion event."""
        node_type = self._get_node_type(node_id)
        
        # Calculate duration if both timestamps are available
        duration_ms = None
        if state.started_at and state.ended_at:
            duration_ms = int((state.ended_at - state.started_at).total_seconds() * 1000)
        
        event = NodeCompletedEvent(
            execution_id=execution_id,
            node_id=node_id,
            node_type=node_type,
            state=state,
            duration_ms=duration_ms,
            token_usage=state.token_usage.model_dump() if state.token_usage else None,
            output_summary=str(state.output)[:100] if state.output else None,  # Brief summary
        )
        await self.event_bus.publish(event)

    async def on_node_error(self, execution_id: str, node_id: str, error: str):
        """Handle node error event."""
        node_type = self._get_node_type(node_id)
        
        event = NodeErrorEvent(
            execution_id=execution_id,
            node_id=node_id,
            node_type=node_type,
            error=error,
            error_type=type(error).__name__ if not isinstance(error, str) else "Error",
            retryable=False,  # TODO: Determine from error type
        )
        await self.event_bus.publish(event)

    async def on_execution_complete(self, execution_id: str):
        """Handle execution completion event."""
        event = ExecutionCompletedEvent(
            execution_id=execution_id,
            status=Status.COMPLETED,
        )
        await self.event_bus.publish(event)

        # Clean up log capture
        if self._log_handler:
            self._cleanup_log_capture()

    async def on_execution_error(self, execution_id: str, error: str):
        """Handle execution error event."""
        event = ExecutionErrorEvent(
            execution_id=execution_id,
            error=error,
            error_type=type(error).__name__ if not isinstance(error, str) else "Error",
        )
        await self.event_bus.publish(event)

        # Clean up log capture
        if self._log_handler:
            self._cleanup_log_capture()

    async def _publish_log_event(self, execution_id: str, log_entry: dict):
        """Publish log event to event bus."""
        event = ExecutionLogEvent(
            execution_id=execution_id,
            level=log_entry["level"],
            message=log_entry["message"],
            logger_name=log_entry["logger"],
            node_id=log_entry.get("node_id"),
            extra_fields={
                "timestamp": log_entry["timestamp"],
            },
        )
        
        try:
            await self.event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish log event: {e}")

    def _get_node_type(self, node_id: str) -> str | None:
        """Get node type from execution runtime if available."""
        if not self.execution_runtime:
            return None

        try:
            from dipeo.diagram_generated import NodeID

            node = self.execution_runtime.get_node(NodeID(node_id))
            if node:
                return node.type.value if hasattr(node.type, "value") else str(node.type)
        except Exception:
            pass

        return None

    def _setup_log_capture(self, execution_id: str):
        """Set up log capture for execution logs."""
        import asyncio
        from datetime import datetime

        class LogCaptureHandler(logging.Handler):
            def __init__(self, observer, exec_id):
                super().__init__()
                self.observer = observer
                self.exec_id = exec_id
                self.setLevel(logging.DEBUG)

            def emit(self, record):
                # Filter noisy logs
                msg = record.getMessage()
                if any(
                    skip in msg
                    for skip in [
                        "APIKeyService",
                        "[ExecutionLogStream]",
                        "POST /graphql",
                    ]
                ):
                    return

                log_entry = {
                    "level": record.levelname,
                    "message": msg,
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "logger": record.name,
                    "node_id": getattr(record, "node_id", None),
                }

                # Publish log asynchronously
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(
                        self.observer._publish_log_event(
                            self.exec_id, log_entry
                        )
                    )
                except RuntimeError:
                    pass  # No event loop available

        self._log_handler = LogCaptureHandler(self, execution_id)

        # Add to relevant loggers
        logging.getLogger("dipeo").addHandler(self._log_handler)
        logging.getLogger("dipeo.application").addHandler(self._log_handler)
        logging.getLogger("dipeo.infra").addHandler(self._log_handler)

    def _cleanup_log_capture(self):
        """Clean up log capture handler."""
        if not self._log_handler:
            return

        # Remove from loggers
        logging.getLogger("dipeo").removeHandler(self._log_handler)
        logging.getLogger("dipeo.application").removeHandler(self._log_handler)
        logging.getLogger("dipeo.infra").removeHandler(self._log_handler)

        self._log_handler = None
