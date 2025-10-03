"""Unified event pipeline for centralized event emission.

This module provides a single, consistent pipeline for all event emission
in the execution engine, ensuring proper metadata, routing, and validation.
"""

import logging
import time
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
    from dipeo.application.execution.state_manager import StateManager
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
    ):
        """Initialize the event pipeline.

        Args:
            execution_id: The execution identifier
            diagram_id: The diagram identifier
            event_bus: The event bus for publishing events
            state_tracker: Optional state tracker for accessing node states
            state_manager: Optional unified state manager for event-sourced state
        """
        self.execution_id = execution_id
        self.diagram_id = diagram_id
        self.event_bus = event_bus
        self.state_tracker = state_tracker
        self.state_manager = state_manager
        self._event_count = 0
        self._start_time = time.time()
        self._sequence_counter = 0  # For idempotency tracking

    async def emit(self, event_type: str, **kwargs) -> None:
        """Generic event emission with automatic routing.

        Args:
            event_type: The type of event to emit
            **kwargs: Event-specific parameters
        """
        # Map event types to specific emission methods
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

    # Public API methods for backward compatibility with EventManager
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
        """Generic event emission (backward compatibility with EventManager).

        Args:
            event_type: The type of event to emit
            data: Optional event metadata
        """
        event = DomainEvent(
            type=event_type,
            scope=EventScope(execution_id=self.execution_id),
            meta=data or {},
        )
        await self._publish(event)

    async def _publish(self, event: DomainEvent) -> None:
        """Publish event through the event bus with metadata and sequence number."""
        # Increment sequence counter for idempotency
        self._sequence_counter += 1

        # Add standard metadata by creating a new event (DomainEvent is frozen)
        meta = event.meta or {}
        meta["pipeline_event_count"] = self._event_count
        meta["pipeline_uptime_ms"] = int((time.time() - self._start_time) * 1000)
        # Add sequence number in metadata for idempotency
        meta["seq"] = self._sequence_counter

        # Create new event with updated metadata and sequence number
        enriched_event = DomainEvent(
            type=event.type,
            scope=event.scope,
            payload=event.payload,
            meta=meta,
        )

        # Publish through event bus (routes to StateStore, MessageRouter, Metrics)
        await self.event_bus.publish(enriched_event)

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
        await self._publish(event)
        # logger.debug(f"[EventPipeline] Execution started: {self.execution_id}")

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

        # Add execution_path to metadata if provided
        if execution_path:
            meta = event.meta or {}
            meta["execution_path"] = execution_path
            event = DomainEvent(
                type=event.type,
                scope=event.scope,
                payload=event.payload,
                meta=meta,
            )

        await self._publish(event)
        # logger.debug(f"[EventPipeline] Execution completed: {self.execution_id}, status: {status}")

    async def _emit_execution_error(self, exc: Exception) -> None:
        """Emit execution error event."""
        event = execution_error(
            execution_id=self.execution_id,
            error_message=str(exc),
            error_type=exc.__class__.__name__,
        )

        # Add diagram_id to metadata
        meta = event.meta or {}
        meta["diagram_id"] = self.diagram_id
        event = DomainEvent(
            type=event.type,
            scope=event.scope,
            payload=event.payload,
            meta=meta,
        )

        await self._publish(event)
        logger.debug(f"[EventPipeline] Execution error: {self.execution_id}, error: {exc}")

    async def _emit_node_started(
        self,
        node: ExecutableNode,
        inputs: dict[str, Any] | None = None,
        iteration: int | None = None,
    ) -> None:
        """Emit node started event."""
        node_state = self._get_node_state(node, Status.RUNNING)

        event = node_started(
            execution_id=self.execution_id,
            node_id=str(node.id),
            state=node_state,
            node_type=str(node.type),
            inputs=inputs,
            iteration=iteration,
        )

        await self._publish(event)
        # logger.debug(f"[EventPipeline] Node started: {node.id}")

    async def _emit_node_completed(
        self,
        node: ExecutableNode,
        envelope: Envelope | None,
        exec_count: int,
        duration_ms: float | None = None,
    ) -> None:
        """Emit node completed event."""
        node_state = self._get_node_state(node, Status.COMPLETED, exec_count)

        # Extract output information
        output = None
        output_summary = None
        token_usage = None
        person_id = None
        model = None
        memory_selection = None

        if envelope:
            output = envelope.body
            output_summary = self._create_output_summary(output)
            token_usage = self._extract_token_usage(envelope)
            # Extract person_id, model, and memory_selection from envelope metadata
            if hasattr(envelope, "meta") and isinstance(envelope.meta, dict):
                person_id = envelope.meta.get("person_id")
                model = envelope.meta.get("model")
                memory_selection = envelope.meta.get("memory_selection")

        event = node_completed(
            execution_id=self.execution_id,
            node_id=str(node.id),
            state=node_state,
            output=output,
            duration_ms=int(duration_ms) if duration_ms else None,
            output_summary=output_summary,
            token_usage=token_usage,
            person_id=person_id,
            model=model,
            memory_selection=memory_selection,
            node_type=str(node.type) if node else None,
        )

        await self._publish(event)
        # logger.debug(
        #     f"[EventPipeline] Node completed: {node.id}, "
        #     f"exec_count: {exec_count}, duration_ms: {duration_ms}"
        # )

    async def _emit_node_error(
        self,
        node: ExecutableNode,
        exc: Exception,
    ) -> None:
        """Emit node error event."""
        node_state = self._get_node_state(node, Status.FAILED)

        event = node_error(
            execution_id=self.execution_id,
            node_id=str(node.id),
            state=node_state,
            error_message=str(exc),
            error_type=exc.__class__.__name__,
        )

        await self._publish(event)
        logger.debug(f"[EventPipeline] Node error: {node.id}, error: {exc}")

        # logger.debug(f"[EventPipeline] Node status changed: {node_id} -> {status}")

    def _get_node_state(
        self,
        node: ExecutableNode,
        status: Status,
        exec_count: int = 0,
    ) -> NodeState:
        """Get or create node state."""
        if self.state_tracker:
            node_state = self.state_tracker.get_node_state(node.id)
            if node_state:
                return node_state

        return NodeState(
            node_id=str(node.id),
            status=status,
            execution_count=exec_count,
        )

    def _create_output_summary(self, output: Any) -> str | None:
        """Create a summary of the output for logging."""
        if output is None:
            return None

        if isinstance(output, str):
            return output[:100] + "..." if len(output) > 100 else output
        elif isinstance(output, dict):
            return f"Object with {len(output)} keys"
        elif isinstance(output, list):
            return f"Array with {len(output)} items"
        else:
            return str(type(output).__name__)

    def _extract_token_usage(self, envelope: Envelope) -> dict | None:
        """Extract token usage from envelope metadata."""
        if not envelope or not hasattr(envelope, "meta") or not isinstance(envelope.meta, dict):
            return None

        llm_usage = envelope.meta.get("llm_usage") or envelope.meta.get("token_usage")
        if not llm_usage:
            return None

        if hasattr(llm_usage, "model_dump"):
            return llm_usage.model_dump()
        elif isinstance(llm_usage, dict):
            return llm_usage

        return None

    def get_stats(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        return {
            "total_events": self._event_count,
            "uptime_seconds": time.time() - self._start_time,
            "execution_id": self.execution_id,
            "diagram_id": self.diagram_id,
        }
