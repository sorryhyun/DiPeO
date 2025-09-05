"""Event publisher facade for simplified domain event emission.

This module provides a convenient facade over the EventBus,
making it easy to emit strongly-typed domain events without manually
constructing event objects.
"""

from typing import Any
from uuid import UUID

from .contracts import (
    DomainEvent,
    EventScope,
    ExecutionCompletedPayload,
    ExecutionErrorPayload,
    ExecutionLogPayload,
    ExecutionStartedPayload,
    MetricsCollectedPayload,
    NodeCompletedPayload,
    NodeErrorPayload,
    NodeOutputPayload,
    NodeStartedPayload,
    WebhookReceivedPayload,
)
from .types import EventType
from .unified_ports import EventBus


class EventPublisher:
    """Facade for publishing domain events with a clean API.

    This class provides convenient methods for emitting all standard domain events,
    handling the construction of event objects and payloads automatically.
    """

    def __init__(self, bus: EventBus):
        """Initialize the publisher with a domain event bus.

        Args:
            bus: The event bus to publish events to
        """
        self.bus = bus

    async def execution_started(
        self,
        execution_id: UUID | str,
        diagram_id: str,
        diagram_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish an execution started event.

        Args:
            execution_id: The execution identifier
            diagram_id: The diagram being executed
            diagram_name: Optional human-readable diagram name
            metadata: Optional metadata for the event
        """
        await self.bus.publish(
            DomainEvent(
                type=EventType.EXECUTION_STARTED,
                scope=EventScope(execution_id=str(execution_id)),
                payload=ExecutionStartedPayload(diagram_id=diagram_id, diagram_name=diagram_name),
                metadata=metadata or {},
            )
        )

    async def execution_completed(
        self,
        execution_id: UUID | str,
        status: str,
        duration_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish an execution completed event.

        Args:
            execution_id: The execution identifier
            status: The final status (SUCCESS, FAILED, etc.)
            duration_ms: Optional execution duration in milliseconds
            metadata: Optional metadata for the event
        """
        await self.bus.publish(
            DomainEvent(
                type=EventType.EXECUTION_COMPLETED,
                scope=EventScope(execution_id=str(execution_id)),
                payload=ExecutionCompletedPayload(status=status, duration_ms=duration_ms),
                metadata=metadata or {},
            )
        )

    async def execution_error(
        self,
        execution_id: UUID | str,
        error_message: str,
        error_type: str | None = None,
        stack_trace: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish an execution error event.

        Args:
            execution_id: The execution identifier
            error_message: The error message
            error_type: Optional error type/class
            stack_trace: Optional stack trace
            metadata: Optional metadata for the event
        """
        await self.bus.publish(
            DomainEvent(
                type=EventType.EXECUTION_ERROR,
                scope=EventScope(execution_id=str(execution_id)),
                payload=ExecutionErrorPayload(
                    error_message=error_message, error_type=error_type, stack_trace=stack_trace
                ),
                metadata=metadata or {},
            )
        )

    async def node_started(
        self,
        execution_id: UUID | str,
        node_id: str,
        node_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a node started event.

        Args:
            execution_id: The execution identifier
            node_id: The node identifier
            node_type: The type of node
            metadata: Optional metadata for the event
        """
        await self.bus.publish(
            DomainEvent(
                type=EventType.NODE_STARTED,
                scope=EventScope(execution_id=str(execution_id), node_id=node_id),
                payload=NodeStartedPayload(node_type=node_type),
                metadata=metadata or {},
            )
        )

    async def node_completed(
        self,
        execution_id: UUID | str,
        node_id: str,
        state: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a node completed event.

        Args:
            execution_id: The execution identifier
            node_id: The node identifier
            state: Optional node output state
            duration_ms: Optional node execution duration
            metadata: Optional metadata for the event
        """
        await self.bus.publish(
            DomainEvent(
                type=EventType.NODE_COMPLETED,
                scope=EventScope(execution_id=str(execution_id), node_id=node_id),
                payload=NodeCompletedPayload(state=state, duration_ms=duration_ms),
                metadata=metadata or {},
            )
        )

    async def node_error(
        self,
        execution_id: UUID | str,
        node_id: str,
        error_message: str,
        error_type: str | None = None,
        stack_trace: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a node error event.

        Args:
            execution_id: The execution identifier
            node_id: The node identifier
            error_message: The error message
            error_type: Optional error type/class
            stack_trace: Optional stack trace
            metadata: Optional metadata for the event
        """
        await self.bus.publish(
            DomainEvent(
                type=EventType.NODE_ERROR,
                scope=EventScope(execution_id=str(execution_id), node_id=node_id),
                payload=NodeErrorPayload(
                    error_message=error_message, error_type=error_type, stack_trace=stack_trace
                ),
                metadata=metadata or {},
            )
        )

    async def node_progress(
        self,
        execution_id: UUID | str,
        node_id: str,
        progress: int,
        message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a node progress event.

        Args:
            execution_id: The execution identifier
            node_id: The node identifier
            progress: Progress percentage (0-100)
            message: Optional progress message
            metadata: Optional metadata for the event
        """
        # Use NodeOutputPayload with progress info as we don't have NodeProgressPayload
        await self.bus.publish(
            DomainEvent(
                type=EventType.NODE_PROGRESS,
                scope=EventScope(execution_id=str(execution_id), node_id=node_id),
                payload=NodeOutputPayload(output={"progress": progress, "message": message}),
                metadata=metadata or {},
            )
        )

    async def execution_update(
        self,
        execution_id: UUID | str,
        message: str,
        level: str = "INFO",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a general execution update event.

        Args:
            execution_id: The execution identifier
            message: The update message
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            metadata: Optional metadata for the event
        """
        # Use ExecutionLogPayload as we don't have ExecutionUpdatePayload
        await self.bus.publish(
            DomainEvent(
                type=EventType.EXECUTION_UPDATE,
                scope=EventScope(execution_id=str(execution_id)),
                payload=ExecutionLogPayload(message=message, level=level),
                metadata=metadata or {},
            )
        )

    async def metrics_collected(
        self,
        execution_id: UUID | str,
        metrics: dict[str, Any],
        node_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a metrics collected event.

        Args:
            execution_id: The execution identifier
            metrics: The collected metrics
            node_id: Optional node identifier if metrics are node-specific
            metadata: Optional metadata for the event
        """
        await self.bus.publish(
            DomainEvent(
                type=EventType.METRICS_COLLECTED,
                scope=EventScope(execution_id=str(execution_id), node_id=node_id),
                payload=MetricsCollectedPayload(metrics=metrics),
                metadata=metadata or {},
            )
        )

    async def webhook_received(
        self,
        execution_id: UUID | str,
        webhook_id: str,
        source: str,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a webhook received event.

        Args:
            execution_id: The execution identifier
            webhook_id: The webhook identifier
            source: The webhook source/provider
            payload: The webhook payload
            metadata: Optional metadata for the event
        """
        await self.bus.publish(
            DomainEvent(
                type=EventType.WEBHOOK_RECEIVED,
                scope=EventScope(execution_id=str(execution_id)),
                payload=WebhookReceivedPayload(webhook_id=webhook_id, source=source, data=payload),
                metadata=metadata or {},
            )
        )

    async def publish_batch(
        self, events: list[tuple[EventType, EventScope, Any, dict[str, Any] | None]]
    ) -> None:
        """Publish multiple events atomically.

        Args:
            events: List of tuples (event_type, scope, payload, metadata)
        """
        domain_events = []
        for event_type, scope, payload, metadata in events:
            domain_events.append(
                DomainEvent(type=event_type, scope=scope, payload=payload, metadata=metadata or {})
            )

        await self.bus.publish_batch(domain_events)
