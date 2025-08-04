"""Unified event observer that publishes all execution events to MessageRouter."""

import logging
from datetime import datetime

from dipeo.core.ports import ExecutionObserver, MessageRouterPort
from dipeo.models import (
    EventType,
    ExecutionStatus,
    NodeExecutionStatus,
    NodeState,
)

try:
    from .scoped_observer import ObserverMetadata
except ImportError:
    from dipeo.application.execution.observers import ObserverMetadata

logger = logging.getLogger(__name__)


class UnifiedEventObserver(ExecutionObserver):
    """Unified observer that publishes all execution events to MessageRouter.

    This observer replaces both MonitoringStreamObserver and EventPublishingObserver,
    providing a single source of truth for real-time execution monitoring.

    Events published through MessageRouter can be consumed by:
    - SSE endpoints (via SSEMessageRouterAdapter)
    - GraphQL subscriptions
    - WebSocket connections
    - Any future real-time transport
    """

    def __init__(
        self, message_router: MessageRouterPort, execution_runtime=None, capture_logs: bool = True
    ):
        self.message_router = message_router
        self.execution_runtime = execution_runtime
        self.capture_logs = capture_logs
        self._log_handler: logging.Handler | None = None

        # Configure metadata for sub-diagram propagation
        self.metadata = ObserverMetadata(
            propagate_to_sub=True,
            scope_to_execution=False,
            filter_events=None,  # Publish all events
        )

    async def on_execution_start(self, execution_id: str, diagram_id: str | None):
        """Handle execution start event."""
        # Set up log capture if enabled
        if self.capture_logs:
            self._setup_log_capture(execution_id)

        await self._publish_event(
            execution_id,
            EventType.EXECUTION_STATUS_CHANGED,
            {
                "status": ExecutionStatus.RUNNING.value,
                "diagram_id": diagram_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def on_node_start(self, execution_id: str, node_id: str):
        """Handle node start event."""
        node_type = self._get_node_type(node_id)

        await self._publish_event(
            execution_id,
            EventType.NODE_STATUS_CHANGED,
            {
                "node_id": node_id,
                "status": NodeExecutionStatus.RUNNING.value,
                "node_type": node_type,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def on_node_complete(self, execution_id: str, node_id: str, state: NodeState):
        """Handle node completion event."""
        node_type = self._get_node_type(node_id)

        await self._publish_event(
            execution_id,
            EventType.NODE_STATUS_CHANGED,
            {
                "node_id": node_id,
                "status": state.status.value,
                "node_type": node_type,
                "output": state.output if state.output else None,
                "started_at": state.started_at.isoformat() if state.started_at else None,
                "ended_at": state.ended_at.isoformat() if state.ended_at else None,
                "token_usage": state.token_usage.model_dump() if state.token_usage else None,
                "tokens_used": state.token_usage.total if state.token_usage else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def on_node_error(self, execution_id: str, node_id: str, error: str):
        """Handle node error event."""
        node_type = self._get_node_type(node_id)

        await self._publish_event(
            execution_id,
            EventType.NODE_STATUS_CHANGED,
            {
                "node_id": node_id,
                "status": NodeExecutionStatus.FAILED.value,
                "node_type": node_type,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def on_execution_complete(self, execution_id: str):
        """Handle execution completion event."""
        await self._publish_event(
            execution_id,
            EventType.EXECUTION_STATUS_CHANGED,
            {
                "status": ExecutionStatus.COMPLETED.value,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Clean up log capture
        if self._log_handler:
            self._cleanup_log_capture()

    async def on_execution_error(self, execution_id: str, error: str):
        """Handle execution error event."""
        await self._publish_event(
            execution_id,
            EventType.EXECUTION_ERROR,
            {
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Clean up log capture
        if self._log_handler:
            self._cleanup_log_capture()

    async def _publish_event(self, execution_id: str, event_type: EventType, data: dict):
        """Publish event to message router."""
        event = {
            "type": event_type.value,
            "execution_id": execution_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            # Broadcast to all connections subscribed to this execution
            await self.message_router.broadcast_to_execution(execution_id, event)
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    def _get_node_type(self, node_id: str) -> str | None:
        """Get node type from execution runtime if available."""
        if not self.execution_runtime:
            return None

        try:
            from dipeo.models import NodeID

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
                        "SSE connection",
                        "EventSourceResponse",
                        "StateRegistry",
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
                    # Use custom event format for logs since EXECUTION_LOG is not in EventType enum
                    log_event = {
                        "type": "EXECUTION_LOG",
                        "execution_id": self.exec_id,
                        "data": log_entry,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    loop.create_task(
                        self.observer.message_router.broadcast_to_execution(
                            self.exec_id, log_event
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
