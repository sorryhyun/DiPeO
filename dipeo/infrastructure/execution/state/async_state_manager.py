"""Async state manager that processes state updates via events."""

import asyncio
import contextlib
import logging
import time
from collections import defaultdict
from typing import Any

from dipeo.diagram_generated import Status
from dipeo.domain.events import DomainEvent, EventType
from dipeo.domain.execution.state.ports import ExecutionStateRepository as StateStorePort

from .execution_state_cache import ExecutionStateCache

logger = logging.getLogger(__name__)


class AsyncStateManager:
    """Processes execution events asynchronously to update state."""

    def __init__(self, state_store: StateStorePort, write_interval: float = 0.05):
        self.state_store = state_store
        self._write_buffer: dict[str, dict[str, Any]] = {}
        self._write_interval = write_interval
        self._write_task: asyncio.Task | None = None
        self._running = False
        self._buffer_lock = asyncio.Lock()
        self._execution_cache = ExecutionStateCache(ttl_seconds=3600)

    async def initialize(self) -> None:
        """Start the async state manager."""
        if self._running:
            return

        self._running = True
        await self._execution_cache.start()
        self._write_task = asyncio.create_task(self._write_loop())

    async def cleanup(self) -> None:
        """Stop the async state manager and flush remaining writes."""
        self._running = False

        if self._write_task:
            self._write_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._write_task

        await self._flush_buffer()
        await self._execution_cache.stop()

    async def handle(self, event: DomainEvent) -> None:
        """Process events asynchronously."""
        execution_id = event.scope.execution_id
        event_type = event.type

        if event_type == EventType.EXECUTION_COMPLETED:
            try:
                await self._persist_events(execution_id, [event])
            except Exception as e:
                logger.error(f"Failed to persist critical event: {e}", exc_info=True)
            return
        async with self._buffer_lock:
            if execution_id not in self._write_buffer:
                self._write_buffer[execution_id] = {"events": [], "last_update": time.time()}

            self._write_buffer[execution_id]["events"].append(event)
            self._write_buffer[execution_id]["last_update"] = time.time()

    async def _write_loop(self) -> None:
        """Batch write to persistent storage."""
        while self._running:
            try:
                await asyncio.sleep(self._write_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                logger.debug("Write loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in write loop: {e}", exc_info=True)

    async def _flush_buffer(self) -> None:
        """Flush buffered events to storage."""
        async with self._buffer_lock:
            if not self._write_buffer:
                return

            for execution_id, buffer in list(self._write_buffer.items()):
                if buffer["events"]:
                    try:
                        await self._persist_events(execution_id, buffer["events"])
                        buffer["events"].clear()
                    except Exception as e:
                        logger.error(
                            f"Failed to persist events for execution {execution_id}: {e}",
                            exc_info=True,
                        )

            self._write_buffer = {
                exec_id: buffer
                for exec_id, buffer in self._write_buffer.items()
                if buffer["events"]
            }

    async def _persist_events(self, execution_id: str, events: list[DomainEvent]) -> None:
        """Persist a batch of events for an execution."""
        events_by_type = defaultdict(list)
        for event in events:
            events_by_type[event.type].append(event)

        if EventType.EXECUTION_STARTED in events_by_type:
            await self._handle_execution_started(
                execution_id, events_by_type[EventType.EXECUTION_STARTED][-1]
            )

        for event in events_by_type.get(EventType.NODE_STARTED, []):
            await self._handle_node_started(execution_id, event)

        for event in events_by_type.get(EventType.NODE_COMPLETED, []):
            await self._handle_node_completed(execution_id, event)

        for event in events_by_type.get(EventType.NODE_ERROR, []):
            await self._handle_node_failed(execution_id, event)

        if EventType.METRICS_COLLECTED in events_by_type:
            await self._handle_metrics_collected(
                execution_id, events_by_type[EventType.METRICS_COLLECTED][-1]
            )

        if EventType.EXECUTION_COMPLETED in events_by_type:
            await self._handle_execution_completed(
                execution_id, events_by_type[EventType.EXECUTION_COMPLETED][-1]
            )

    async def _handle_execution_started(self, execution_id: str, event: DomainEvent) -> None:
        """Handle execution started event."""
        payload = event.payload
        diagram_id = getattr(payload, "diagram_id", None) if payload else None
        variables = getattr(payload, "variables", {}) if payload else {}

        cache = await self._execution_cache.get_cache(execution_id)
        existing_state = await self.state_store.get_state(execution_id)

        if not existing_state:
            state = await self.state_store.create_execution(
                execution_id=execution_id, diagram_id=diagram_id, variables=variables
            )
            await cache.set_state(state)
        else:
            await cache.set_state(existing_state)

        await self.state_store.update_status(execution_id=execution_id, status=Status.RUNNING)

    async def _handle_node_started(self, execution_id: str, event: DomainEvent) -> None:
        """Handle node started event."""
        node_id = event.scope.node_id
        if not node_id:
            return

        await self.state_store.update_node_status(
            execution_id=execution_id, node_id=node_id, status=Status.RUNNING
        )

    async def _handle_node_completed(self, execution_id: str, event: DomainEvent) -> None:
        """Handle node completed event."""
        node_id = event.scope.node_id
        payload = event.payload

        data = {
            "node_id": node_id,
            "state": getattr(payload, "state", None) if payload else None,
            "output": getattr(payload, "output", None) if payload else None,
            "metrics": {"llm_usage": getattr(payload, "llm_usage", None)}
            if payload and hasattr(payload, "llm_usage")
            else {},
        }
        if not node_id:
            return

        cache = await self._execution_cache.get_cache(execution_id)

        output = data.get("output")
        if output is not None:
            await cache.set_node_output(node_id, output)

            llm_usage = data.get("metrics", {}).get("llm_usage")
            await self.state_store.update_node_output(
                execution_id=execution_id, node_id=node_id, output=output, llm_usage=llm_usage
            )

        await cache.set_node_status(node_id, Status.COMPLETED)
        await self.state_store.update_node_status(
            execution_id=execution_id, node_id=node_id, status=Status.COMPLETED
        )

    async def _handle_node_failed(self, execution_id: str, event: DomainEvent) -> None:
        """Handle node failed event."""
        node_id = event.scope.node_id
        payload = event.payload

        data = {
            "node_id": node_id,
            "error": getattr(payload, "error_message", "Unknown error")
            if payload
            else "Unknown error",
        }
        if not node_id:
            return

        error = data.get("error", "Unknown error")

        await self.state_store.update_node_status(
            execution_id=execution_id, node_id=node_id, status=Status.FAILED, error=error
        )
        await self.state_store.update_node_output(
            execution_id=execution_id, node_id=node_id, output={"error": error}, is_exception=True
        )

    async def _handle_metrics_collected(self, execution_id: str, event: DomainEvent) -> None:
        """Handle metrics collected event."""
        payload = event.payload
        metrics = getattr(payload, "metrics", {}) if payload else {}

        if metrics:
            await self.state_store.update_metrics(execution_id=execution_id, metrics=metrics)
            logger.debug(f"Saved metrics for execution {execution_id}")

    async def _handle_execution_completed(self, execution_id: str, event: DomainEvent) -> None:
        """Handle execution completed event."""
        payload = event.payload
        status = getattr(payload, "status", Status.COMPLETED) if payload else Status.COMPLETED
        error = None
        if event.type == EventType.EXECUTION_ERROR and payload:
            error = getattr(payload, "error_message", None)

        await self.state_store.update_status(execution_id=execution_id, status=status, error=error)

        state = await self.state_store.get_state(execution_id)
        if state:
            await self.state_store.persist_final_state(state)
