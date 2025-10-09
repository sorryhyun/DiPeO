"""Core event pipeline for centralized event emission."""

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.events.builders import (
    create_output_summary,
    extract_envelope_metadata,
    extract_token_usage,
    get_node_state,
)
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import Status
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
    from dipeo.application.execution.states.state_manager import StateManager
    from dipeo.domain.execution.state_tracker import StateTracker

logger = get_module_logger(__name__)


class EventPipeline:
    """Centralized event pipeline for all execution events.

    This class handles:
    - Consistent event creation with standard metadata
    - Event validation
    - Automatic routing to StateStore, MessageRouter, and Metrics
    - Unified event flow tracking
    """

    def __init__(
        self,
        execution_id: str,
        diagram_id: str,
        event_bus: EventBus,
        state_tracker: Optional["StateTracker"] = None,
        state_manager: Optional["StateManager"] = None,
        parent_execution_id: Optional[str] = None,
    ):
        """Initialize the event pipeline."""
        self.execution_id = execution_id
        self.diagram_id = diagram_id
        self.event_bus = event_bus
        self.state_tracker = state_tracker
        self.state_manager = state_manager
        self.parent_execution_id = parent_execution_id
        self._event_count = 0
        self._start_time = time.time()
        self._sequence_counter = 0
        self._background_tasks: set[asyncio.Task] = set()

    async def emit(self, event_type: str, **kwargs) -> None:
        """Generic event emission with automatic routing."""
        emission_map = {
            "execution_started": self._emit_execution_started,
            "execution_completed": self._emit_execution_completed,
            "execution_error": self._emit_execution_error,
            "node_started": self._emit_node_started,
            "node_completed": self._emit_node_completed,
            "node_error": self._emit_node_error,
        }

        handler = emission_map.get(event_type)
        if not handler:
            logger.warning(f"Unknown event type: {event_type}")
            return

        await handler(**kwargs)
        self._event_count += 1

    async def emit_execution_started(
        self,
        diagram_name: str | None = None,
        variables: dict[str, Any] | None = None,
        initiated_by: str | None = None,
    ) -> None:
        """Emit execution started event (public API)."""
        await self._emit_execution_started(diagram_name, variables, initiated_by)

    async def emit_execution_completed(
        self,
        status: Status = Status.COMPLETED,
        total_steps: int = 0,
        execution_path: list[str] | None = None,
        total_duration_ms: int | None = None,
        total_tokens_used: int | None = None,
    ) -> None:
        """Emit execution completed event (public API)."""
        await self._emit_execution_completed(
            status, total_steps, execution_path, total_duration_ms, total_tokens_used
        )

    async def emit_execution_error(self, exc: Exception) -> None:
        """Emit execution error event (public API)."""
        await self._emit_execution_error(exc)

    async def emit_node_started(
        self,
        node: ExecutableNode,
        inputs: dict[str, Any] | None = None,
        iteration: int | None = None,
    ) -> None:
        """Emit node started event (public API)."""
        await self._emit_node_started(node, inputs, iteration)

    async def emit_node_completed(
        self,
        node: ExecutableNode,
        envelope: Envelope | None,
        exec_count: int,
        duration_ms: float | None = None,
    ) -> None:
        """Emit node completed event (public API)."""
        await self._emit_node_completed(node, envelope, exec_count, duration_ms)

    async def emit_node_error(
        self,
        node: ExecutableNode,
        exc: Exception,
    ) -> None:
        """Emit node error event (public API)."""
        await self._emit_node_error(node, exc)

    async def emit_event(self, event_type: EventType, data: dict[str, Any] | None = None) -> None:
        """Generic event emission (backward compatibility with EventManager)."""
        event = DomainEvent(
            type=event_type,
            scope=EventScope(execution_id=self.execution_id),
            meta=data or {},
        )
        self._publish(event)

    def _publish(self, event: DomainEvent) -> None:
        """Publish event through the event bus with metadata and sequence number (fire-and-forget)."""
        self._sequence_counter += 1

        meta = event.meta or {}
        meta["pipeline_event_count"] = self._event_count
        meta["pipeline_uptime_ms"] = int((time.time() - self._start_time) * 1000)
        meta["seq"] = self._sequence_counter

        enriched_event = DomainEvent(
            type=event.type,
            scope=event.scope,
            payload=event.payload,
            meta=meta,
        )

        task = asyncio.create_task(self._publish_async(enriched_event))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _publish_async(self, event: DomainEvent) -> None:
        """Asynchronously publish event to event bus."""
        try:
            await self.event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish event {event.type}: {e}", exc_info=True)

    async def wait_for_pending_events(self) -> None:
        """Wait for all pending background event publishing tasks to complete."""
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

    async def _emit_execution_started(
        self,
        diagram_name: str | None = None,
        variables: dict[str, Any] | None = None,
        initiated_by: str | None = None,
    ) -> None:
        """Emit execution started event."""
        event = execution_started(
            execution_id=self.execution_id,
            diagram_id=self.diagram_id or diagram_name,
            variables=variables or {},
            initiated_by=initiated_by,
        )
        # Set parent_execution_id in scope if this is a child execution
        if self.parent_execution_id:
            event = DomainEvent(
                type=event.type,
                scope=EventScope(
                    execution_id=self.execution_id,
                    parent_execution_id=self.parent_execution_id,
                ),
                payload=event.payload,
                meta=event.meta,
            )
        self._publish(event)

    async def _emit_execution_completed(
        self,
        status: Status = Status.COMPLETED,
        total_steps: int = 0,
        execution_path: list[str] | None = None,
        total_duration_ms: int | None = None,
        total_tokens_used: int | None = None,
    ) -> None:
        """Emit execution completed event."""
        event = execution_completed(
            execution_id=self.execution_id,
            status=status,
            total_duration_ms=total_duration_ms,
            total_tokens_used=total_tokens_used,
            node_count=total_steps,
        )

        meta = event.meta or {}
        if execution_path:
            meta["execution_path"] = execution_path

        # Set parent_execution_id in scope if this is a child execution
        if self.parent_execution_id:
            event = DomainEvent(
                type=event.type,
                scope=EventScope(
                    execution_id=self.execution_id,
                    parent_execution_id=self.parent_execution_id,
                ),
                payload=event.payload,
                meta=meta,
            )
        elif execution_path:
            event = DomainEvent(
                type=event.type,
                scope=event.scope,
                payload=event.payload,
                meta=meta,
            )

        self._publish(event)

    async def _emit_execution_error(self, exc: Exception) -> None:
        """Emit execution error event."""
        event = execution_error(
            execution_id=self.execution_id,
            error_message=str(exc),
            error_type=exc.__class__.__name__,
        )

        meta = event.meta or {}
        meta["diagram_id"] = self.diagram_id
        event = DomainEvent(
            type=event.type,
            scope=event.scope,
            payload=event.payload,
            meta=meta,
        )

        self._publish(event)
        logger.debug(f"[EventPipeline] Execution error: {self.execution_id}, error: {exc}")

    async def _emit_node_started(
        self,
        node: ExecutableNode,
        inputs: dict[str, Any] | None = None,
        iteration: int | None = None,
    ) -> None:
        """Emit node started event."""
        node_state = get_node_state(node, Status.RUNNING, state_tracker=self.state_tracker)

        event = node_started(
            execution_id=self.execution_id,
            node_id=str(node.id),
            state=node_state,
            node_type=str(node.type),
            inputs=inputs,
            iteration=iteration,
        )

        self._publish(event)

    async def _emit_node_completed(
        self,
        node: ExecutableNode,
        envelope: Envelope | None,
        exec_count: int,
        duration_ms: float | None = None,
    ) -> None:
        """Emit node completed event."""
        node_state = get_node_state(
            node, Status.COMPLETED, exec_count, state_tracker=self.state_tracker
        )

        output = envelope.body if envelope else None
        output_summary = create_output_summary(output)
        token_usage = extract_token_usage(envelope)
        envelope_meta = extract_envelope_metadata(envelope)

        event = node_completed(
            execution_id=self.execution_id,
            node_id=str(node.id),
            state=node_state,
            output=output,
            duration_ms=int(duration_ms) if duration_ms else None,
            output_summary=output_summary,
            token_usage=token_usage,
            person_id=envelope_meta.get("person_id"),
            model=envelope_meta.get("model"),
            memory_selection=envelope_meta.get("memory_selection"),
            node_type=str(node.type) if node else None,
        )

        self._publish(event)

    async def _emit_node_error(
        self,
        node: ExecutableNode,
        exc: Exception,
    ) -> None:
        """Emit node error event."""
        node_state = get_node_state(node, Status.FAILED, state_tracker=self.state_tracker)

        event = node_error(
            execution_id=self.execution_id,
            node_id=str(node.id),
            state=node_state,
            error_message=str(exc),
            error_type=exc.__class__.__name__,
        )

        self._publish(event)
        logger.debug(f"[EventPipeline] Node error: {node.id}, error: {exc}")

    def get_stats(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        return {
            "total_events": self._event_count,
            "uptime_seconds": time.time() - self._start_time,
            "execution_id": self.execution_id,
            "diagram_id": self.diagram_id,
        }
