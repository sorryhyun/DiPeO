"""Async state manager that processes state updates via events."""

import asyncio
import contextlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from dipeo.diagram_generated import Status
from dipeo.domain.events import DomainEvent, EventType
from dipeo.domain.execution.state.ports import ExecutionStateRepository as StateStorePort

from .execution_state_cache import ExecutionStateCache

logger = logging.getLogger(__name__)


@dataclass
class BatchUpdate:
    """Represents a batch of updates for a single execution."""

    execution_id: str
    node_status_updates: dict[str, tuple[Status, str | None]] = field(default_factory=dict)
    node_output_updates: dict[str, Any] = field(default_factory=dict)
    execution_status: tuple[Status, str | None] | None = None
    metrics: dict[str, Any] | None = None
    last_update_time: float = field(default_factory=time.time)


class AsyncStateManager:
    """Processes execution events asynchronously to update state with batching."""

    def __init__(self, state_store: StateStorePort, write_interval: float = 0.1):
        self.state_store = state_store
        self._write_buffer: dict[str, BatchUpdate] = {}
        self._write_interval = write_interval
        self._write_task: asyncio.Task | None = None
        self._running = False
        self._buffer_lock = asyncio.Lock()
        self._execution_cache = ExecutionStateCache(ttl_seconds=3600)

        # Metrics for monitoring
        self._total_writes = 0
        self._total_batches = 0
        self._total_events_processed = 0
        self._batch_sizes: list[int] = []

    async def initialize(self) -> None:
        """Start the async state manager."""
        if self._running:
            return

        self._running = True
        await self._execution_cache.start()
        self._write_task = asyncio.create_task(self._write_loop())
        self._metrics_task = asyncio.create_task(self._metrics_loop())

    async def cleanup(self) -> None:
        """Stop the async state manager and flush remaining writes."""
        self._running = False

        if self._write_task:
            self._write_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._write_task

        if hasattr(self, "_metrics_task") and self._metrics_task:
            self._metrics_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._metrics_task

        await self._flush_buffer()
        await self._execution_cache.stop()
        self._log_final_metrics()

    async def handle(self, event: DomainEvent) -> None:
        """Process events asynchronously with batching."""
        execution_id = event.scope.execution_id
        event_type = event.type
        self._total_events_processed += 1

        # Critical events bypass batching for immediate persistence
        if event_type == EventType.EXECUTION_COMPLETED:
            try:
                await self._process_event_immediately(execution_id, event)
                await self._flush_execution(execution_id)
            except Exception as e:
                logger.error(f"Failed to persist critical event: {e}", exc_info=True)
            return

        # Batch non-critical events
        async with self._buffer_lock:
            if execution_id not in self._write_buffer:
                self._write_buffer[execution_id] = BatchUpdate(execution_id=execution_id)

            batch = self._write_buffer[execution_id]
            batch.last_update_time = time.time()

            # Add event to appropriate batch category
            if event_type == EventType.NODE_STARTED:
                node_id = event.scope.node_id
                if node_id:
                    batch.node_status_updates[node_id] = (Status.RUNNING, None)
            elif event_type == EventType.NODE_COMPLETED:
                node_id = event.scope.node_id
                if node_id and event.payload:
                    batch.node_status_updates[node_id] = (Status.COMPLETED, None)
                    output = getattr(event.payload, "output", None)
                    if output is not None:
                        batch.node_output_updates[node_id] = output
            elif event_type == EventType.NODE_ERROR:
                node_id = event.scope.node_id
                if node_id:
                    error = (
                        getattr(event.payload, "error_message", "Unknown error")
                        if event.payload
                        else "Unknown error"
                    )
                    batch.node_status_updates[node_id] = (Status.FAILED, error)
                    batch.node_output_updates[node_id] = {"error": error}
            elif event_type == EventType.EXECUTION_STARTED:
                batch.execution_status = (Status.RUNNING, None)
            elif event_type == EventType.METRICS_COLLECTED:
                if event.payload:
                    batch.metrics = getattr(event.payload, "metrics", {})

    async def _write_loop(self) -> None:
        """Batch write to persistent storage with adaptive intervals."""
        consecutive_empty_flushes = 0
        adaptive_interval = self._write_interval

        while self._running:
            try:
                await asyncio.sleep(adaptive_interval)

                # Track buffer size before flush
                buffer_size = len(self._write_buffer)
                await self._flush_buffer()

                # Adaptive batching based on load
                if buffer_size == 0:
                    consecutive_empty_flushes += 1
                    # Increase interval if no activity (up to 2x base interval)
                    if consecutive_empty_flushes > 3:
                        adaptive_interval = min(self._write_interval * 2, 0.4)
                else:
                    consecutive_empty_flushes = 0
                    # High load: decrease interval (down to 0.5x base interval)
                    if buffer_size > 10:
                        adaptive_interval = max(self._write_interval * 0.5, 0.05)
                    else:
                        adaptive_interval = self._write_interval

            except asyncio.CancelledError:
                logger.debug("Write loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in write loop: {e}", exc_info=True)

    async def _metrics_loop(self) -> None:
        """Periodically log metrics for monitoring."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Log metrics every minute
                self._log_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics loop: {e}", exc_info=True)

    def _log_metrics(self) -> None:
        """Log current performance metrics."""
        if self._batch_sizes:
            avg_batch_size = sum(self._batch_sizes) / len(self._batch_sizes)
            max_batch_size = max(self._batch_sizes)
        else:
            avg_batch_size = 0
            max_batch_size = 0

        logger.info(
            f"AsyncStateManager metrics - "
            f"Total events: {self._total_events_processed}, "
            f"Total writes: {self._total_writes}, "
            f"Total batches: {self._total_batches}, "
            f"Avg batch size: {avg_batch_size:.1f}, "
            f"Max batch size: {max_batch_size}, "
            f"Active buffers: {len(self._write_buffer)}"
        )

        # Reset batch size tracking
        if len(self._batch_sizes) > 100:
            self._batch_sizes = self._batch_sizes[-50:]

    def _log_final_metrics(self) -> None:
        """Log final metrics on shutdown."""
        if self._total_events_processed > 0:
            write_reduction = (1 - (self._total_writes / self._total_events_processed)) * 100
            logger.info(
                f"AsyncStateManager final metrics - "
                f"Processed {self._total_events_processed} events with {self._total_writes} writes "
                f"({write_reduction:.1f}% write reduction through batching)"
            )

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics for external monitoring."""
        return {
            "total_events_processed": self._total_events_processed,
            "total_writes": self._total_writes,
            "total_batches": self._total_batches,
            "avg_batch_size": sum(self._batch_sizes) / len(self._batch_sizes)
            if self._batch_sizes
            else 0,
            "active_buffers": len(self._write_buffer),
            "write_interval": self._write_interval,
        }

    async def _flush_buffer(self) -> None:
        """Flush buffered updates to storage using bulk operations."""
        async with self._buffer_lock:
            if not self._write_buffer:
                return

            current_time = time.time()
            executions_to_flush = []

            # Identify which executions need flushing
            for execution_id, batch in self._write_buffer.items():
                # Flush if there are updates and enough time has passed
                time_since_update = current_time - batch.last_update_time
                if time_since_update >= self._write_interval:
                    if (
                        batch.node_status_updates
                        or batch.node_output_updates
                        or batch.execution_status
                        or batch.metrics
                    ):
                        executions_to_flush.append(execution_id)

            # Flush identified executions
            for execution_id in executions_to_flush:
                batch = self._write_buffer[execution_id]
                try:
                    await self._persist_batch(batch)
                    self._total_batches += 1
                    self._batch_sizes.append(
                        len(batch.node_status_updates) + len(batch.node_output_updates)
                    )
                    # Remove flushed batch
                    del self._write_buffer[execution_id]
                except Exception as e:
                    logger.error(
                        f"Failed to persist batch for execution {execution_id}: {e}",
                        exc_info=True,
                    )

    async def _flush_execution(self, execution_id: str) -> None:
        """Force flush a specific execution."""
        async with self._buffer_lock:
            if execution_id in self._write_buffer:
                batch = self._write_buffer[execution_id]
                try:
                    await self._persist_batch(batch)
                    del self._write_buffer[execution_id]
                except Exception as e:
                    logger.error(
                        f"Failed to flush execution {execution_id}: {e}",
                        exc_info=True,
                    )

    async def _persist_batch(self, batch: BatchUpdate) -> None:
        """Persist a batch of updates using bulk operations."""
        execution_id = batch.execution_id
        cache = await self._execution_cache.get_cache(execution_id)

        # Get current state
        state = await cache.get_state()
        if not state:
            state = await self.state_store.get_state(execution_id)
            if not state:
                # Handle execution started if needed
                if batch.execution_status and batch.execution_status[0] == Status.RUNNING:
                    state = await self.state_store.create_execution(
                        execution_id=execution_id,
                        diagram_id=None,
                        variables={},
                    )
                    await cache.set_state(state)
                else:
                    logger.warning(f"No state found for execution {execution_id}")
                    return

        # Apply batch updates to state object
        state_modified = False

        # Update node statuses in bulk
        if batch.node_status_updates:
            for node_id, (status, error) in batch.node_status_updates.items():
                await cache.set_node_status(node_id, status, error)
                # Update state object
                from datetime import datetime

                from dipeo.diagram_generated import NodeState

                now = datetime.now().isoformat()
                if node_id not in state.node_states:
                    state.node_states[node_id] = NodeState(
                        status=status,
                        started_at=now if status == Status.RUNNING else None,
                        ended_at=now if status in [Status.COMPLETED, Status.FAILED] else None,
                        error=error,
                        llm_usage=None,
                    )
                else:
                    state.node_states[node_id].status = status
                    if status == Status.RUNNING:
                        state.node_states[node_id].started_at = now
                    elif status in [Status.COMPLETED, Status.FAILED]:
                        state.node_states[node_id].ended_at = now
                    if error:
                        state.node_states[node_id].error = error

                if status == Status.RUNNING and node_id not in state.executed_nodes:
                    state.executed_nodes.append(node_id)

                state_modified = True
                self._total_writes += 1

        # Update node outputs in bulk
        if batch.node_output_updates:
            for node_id, output in batch.node_output_updates.items():
                await cache.set_node_output(node_id, output)
                # Serialize output properly
                if hasattr(output, "to_dict"):
                    from dipeo.infrastructure.execution.utils import serialize_protocol

                    serialized_output = serialize_protocol(output)
                else:
                    serialized_output = output
                state.node_outputs[node_id] = serialized_output
                state_modified = True
                self._total_writes += 1

        # Update execution status
        if batch.execution_status:
            status, error = batch.execution_status
            state.status = status
            if error:
                state.error = error
            state_modified = True

        # Update metrics
        if batch.metrics:
            if not state.metrics:
                state.metrics = {}
            state.metrics.update(batch.metrics)
            state_modified = True

        # Persist state if modified
        if state_modified:
            await self.state_store.save_state(state)

    async def _process_event_immediately(self, execution_id: str, event: DomainEvent) -> None:
        """Process critical events immediately without batching."""
        if event.type == EventType.EXECUTION_COMPLETED:
            await self._handle_execution_completed(execution_id, event)

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
