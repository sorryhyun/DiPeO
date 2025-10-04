"""Event management for execution context.

DEPRECATED: This module is deprecated. Use EventPipeline from
dipeo.application.execution.event_pipeline instead, which provides
the same interface with enhanced features (sequence tracking, metrics).

This module provides focused event operations as a domain concern,
managing the emission of execution and node lifecycle events.
"""

import logging
import warnings
from typing import TYPE_CHECKING, Any, Optional

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import NodeID, NodeState, Status
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.domain.events import (
    DomainEvent,
    EventScope,
    EventType,
    execution_completed,
    execution_error,
    execution_started,
    node_completed,
    node_error,
    node_started,
)
from dipeo.domain.events.unified_ports import EventBus
from dipeo.domain.execution.envelope import Envelope

if TYPE_CHECKING:
    from dipeo.domain.execution.state_tracker import StateTracker

logger = get_module_logger(__name__)


class EventManager:
    """Manages event emission for execution context.

    DEPRECATED: Use EventPipeline from dipeo.application.execution.events
    instead. EventPipeline provides the same interface with enhanced features:
    - Sequence tracking for idempotency
    - Event metrics and statistics
    - Enhanced metadata management

    Responsibilities:
    - Execution lifecycle events
    - Node execution events
    - Status change notifications
    - Event bus integration

    This is a domain component that encapsulates event emission logic,
    using typed domain events instead of ad-hoc dictionaries.
    """

    def __init__(
        self,
        execution_id: str,
        diagram_id: str,
        event_bus: EventBus | None = None,
        state_tracker: Optional["StateTracker"] = None,
    ):
        """Initialize the event manager.

        DEPRECATED: Use EventPipeline instead.

        Args:
            execution_id: The execution identifier
            diagram_id: The diagram identifier
            event_bus: Optional event bus for publishing events
            state_tracker: Optional state tracker for accessing node states
        """
        warnings.warn(
            "EventManager is deprecated. Use EventPipeline from "
            "dipeo.application.execution.event_pipeline instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.execution_id = execution_id
        self.diagram_id = diagram_id
        self.event_bus = event_bus
        self.state_tracker = state_tracker

    async def _publish(self, event: DomainEvent) -> None:
        if self.event_bus:
            await self.event_bus.publish(event)

    async def emit_execution_started(
        self,
        diagram_name: str | None = None,
        variables: dict[str, Any] | None = None,
        initiated_by: str | None = None,
    ) -> None:
        event = execution_started(
            execution_id=self.execution_id,
            diagram_id=self.diagram_id or diagram_name,
            variables=variables or {},
            initiated_by=initiated_by,
        )
        await self._publish(event)

    async def emit_execution_completed(
        self,
        status: Status = Status.COMPLETED,
        total_steps: int = 0,
        execution_path: list[str] | None = None,
        total_duration_ms: int | None = None,
        total_tokens_used: int | None = None,
    ) -> None:
        event = execution_completed(
            execution_id=self.execution_id,
            status=status,
            total_duration_ms=total_duration_ms,
            total_tokens_used=total_tokens_used,
            node_count=total_steps,
        )
        if execution_path:
            event = DomainEvent(
                type=event.type,
                scope=event.scope,
                payload=event.payload,
                meta={"execution_path": execution_path},
            )
        await self._publish(event)

    async def emit_execution_error(self, exc: Exception) -> None:
        event = execution_error(
            execution_id=self.execution_id,
            error_message=str(exc),
            error_type=exc.__class__.__name__,
        )
        event = DomainEvent(
            type=event.type,
            scope=event.scope,
            payload=event.payload,
            meta={"diagram_id": self.diagram_id},
        )
        await self._publish(event)

    async def emit_node_started(
        self,
        node: ExecutableNode,
        inputs: dict[str, Any] | None = None,
        iteration: int | None = None,
    ) -> None:
        node_state = None
        if self.state_tracker:
            node_state = self.state_tracker.get_node_state(node.id)

        if not node_state:
            node_state = NodeState(
                node_id=str(node.id),
                status=Status.RUNNING,
                execution_count=0,
            )

        event = node_started(
            execution_id=self.execution_id,
            node_id=str(node.id),
            state=node_state,
            node_type=str(node.type),
            inputs=inputs,
            iteration=iteration,
        )
        await self._publish(event)

    async def emit_node_completed(
        self,
        node: ExecutableNode,
        envelope: Envelope | None,
        exec_count: int,
        duration_ms: int | None = None,
    ) -> None:
        node_state = None
        if self.state_tracker:
            node_state = self.state_tracker.get_node_state(node.id)

        if not node_state:
            node_state = NodeState(
                node_id=str(node.id),
                status=Status.COMPLETED,
                execution_count=exec_count,
            )

        output = None
        output_summary = None
        token_usage = None
        if envelope:
            output = envelope.body
            if isinstance(output, str):
                output_summary = output[:100] + "..." if len(output) > 100 else output
            elif isinstance(output, dict):
                output_summary = f"Object with {len(output)} keys"
            elif isinstance(output, list):
                output_summary = f"Array with {len(output)} items"

            if hasattr(envelope, "meta") and isinstance(envelope.meta, dict):
                llm_usage = envelope.meta.get("llm_usage") or envelope.meta.get("token_usage")
                if llm_usage:
                    if hasattr(llm_usage, "model_dump"):
                        token_usage = llm_usage.model_dump()
                    elif isinstance(llm_usage, dict):
                        token_usage = llm_usage

                    if token_usage:
                        import logging

                        from dipeo.config.base_logger import get_module_logger

                        logger = get_module_logger(__name__)
                        logger.debug(
                            f"[EventManager] Emitting NODE_COMPLETED with token_usage: {token_usage}"
                        )

        event = node_completed(
            execution_id=self.execution_id,
            node_id=str(node.id),
            state=node_state,
            output=output,
            duration_ms=duration_ms,
            output_summary=output_summary,
            token_usage=token_usage,
        )
        await self._publish(event)

    async def emit_node_error(
        self,
        node: ExecutableNode,
        exc: Exception,
        retryable: bool = False,
        retry_count: int = 0,
    ) -> None:
        node_state = None
        if self.state_tracker:
            node_state = self.state_tracker.get_node_state(node.id)

        if not node_state:
            node_state = NodeState(
                node_id=str(node.id),
                status=Status.FAILED,
                execution_count=0,
                error=str(exc),
            )

        event = node_error(
            execution_id=self.execution_id,
            node_id=str(node.id),
            state=node_state,
            error_message=str(exc),
            error_type=exc.__class__.__name__,
            retryable=retryable,
            retry_count=retry_count,
        )
        await self._publish(event)

    async def emit_event(self, event_type: EventType, data: dict[str, Any] | None = None) -> None:
        if self.event_bus:
            from dipeo.domain.events import EventScope

            event = DomainEvent(
                type=event_type, scope=EventScope(execution_id=self.execution_id), meta=data or {}
            )
            await self._publish(event)
