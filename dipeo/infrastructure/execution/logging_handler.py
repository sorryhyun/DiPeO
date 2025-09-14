"""Logging handler that emits EXECUTION_LOG events to the event bus."""

import contextlib
import logging

from dipeo.domain.events import DomainEvent, EventScope, EventType
from dipeo.domain.events.contracts import ExecutionLogPayload
from dipeo.domain.events.unified_ports import EventBus


class ExecutionLogHandler(logging.Handler):
    """Logging handler that emits logs as domain events for real-time monitoring.

    This handler captures Python logging output during execution and converts it
    to EXECUTION_LOG events that can be consumed by the browser via GraphQL subscriptions.
    """

    def __init__(self, event_bus: EventBus, execution_id: str | None = None):
        """Initialize the handler with an event bus.

        Args:
            event_bus: The domain event bus to emit log events to
            execution_id: Optional execution ID to associate with all logs
        """
        super().__init__()
        self.event_bus = event_bus
        self.execution_id = execution_id
        self._enabled = True

    def set_execution_id(self, execution_id: str) -> None:
        """Set the execution ID for subsequent log events."""
        self.execution_id = execution_id

    def clear_execution_id(self) -> None:
        """Clear the execution ID."""
        self.execution_id = None

    def enable(self) -> None:
        """Enable event emission."""
        self._enabled = True

    def disable(self) -> None:
        """Disable event emission (useful during cleanup)."""
        self._enabled = False

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record as a domain event.

        Args:
            record: The log record to emit
        """
        if not self._enabled or not self.execution_id:
            return

        try:
            msg = self.format(record)
            level = record.levelname
            import asyncio

            event = DomainEvent(
                type=EventType.EXECUTION_LOG,
                scope=EventScope(execution_id=self.execution_id),
                payload=ExecutionLogPayload(
                    message=msg,
                    level=level,
                    logger_name=record.name,
                    extra_fields={"timestamp": record.created},
                ),
            )

            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return

            task = asyncio.create_task(self._emit_async(event))
            _ = task

        except Exception:
            self.handleError(record)

    async def _emit_async(self, event: DomainEvent) -> None:
        """Emit the event asynchronously.

        Args:
            event: The domain event to emit
        """
        with contextlib.suppress(Exception):
            await self.event_bus.publish(event)


def setup_execution_logging(
    event_bus: EventBus, execution_id: str, log_level: int = logging.INFO
) -> ExecutionLogHandler:
    """Set up logging for an execution.

    This adds an ExecutionLogHandler to the root logger that will emit
    all log messages as EXECUTION_LOG events.

    Args:
        event_bus: The domain event bus to emit events to
        execution_id: The execution ID to associate with logs
        log_level: The minimum log level to emit (default: INFO)

    Returns:
        The created handler (for later removal)
    """
    handler = ExecutionLogHandler(event_bus, execution_id)
    handler.setLevel(log_level)

    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    return handler


def teardown_execution_logging(handler: ExecutionLogHandler) -> None:
    """Remove the execution logging handler.

    Args:
        handler: The handler to remove
    """
    handler.disable()
    logging.getLogger().removeHandler(handler)
