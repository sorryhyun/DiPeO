"""Metrics collection observer for execution analysis."""

import asyncio
import contextlib
import logging
import time
from typing import TYPE_CHECKING, Any, cast

from dipeo.application.execution.observers.metrics_analysis import MetricsAnalyzer
from dipeo.application.execution.observers.metrics_types import (
    ExecutionMetrics as DataclassExecutionMetrics,
)
from dipeo.application.execution.observers.metrics_types import NodeMetrics as DataclassNodeMetrics
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import (
    Bottleneck,
)
from dipeo.diagram_generated import (
    ExecutionMetrics as PydanticExecutionMetrics,
)
from dipeo.diagram_generated import NodeMetrics as PydanticNodeMetrics
from dipeo.domain.events import (
    DomainEvent,
    EventBus,
    EventType,
    NodeCompletedPayload,
    NodeErrorPayload,
    NodeStartedPayload,
)
from dipeo.infrastructure.timing.collector import timing_collector

if TYPE_CHECKING:
    from dipeo.domain.execution.state.ports import ExecutionStateRepository

logger = get_module_logger(__name__)


class MetricsObserver(EventBus):
    """Collects execution metrics for analysis and optimization suggestions."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        state_store: "ExecutionStateRepository | None" = None,
    ):
        self._metrics_buffer: dict[str, DataclassExecutionMetrics] = {}
        self._completed_metrics: dict[str, DataclassExecutionMetrics] = {}
        self.event_bus = event_bus
        self.state_store = state_store
        self._cleanup_task: asyncio.Task | None = None
        self._running = False
        self._max_completed_metrics = 10

        self._analyzer = MetricsAnalyzer(event_bus=event_bus, analysis_threshold_ms=1000)

    def get_execution_metrics(self, execution_id: str) -> DataclassExecutionMetrics | None:
        """Get metrics for a specific execution."""
        return self._metrics_buffer.get(execution_id) or self._completed_metrics.get(execution_id)

    def get_all_metrics(self) -> dict[str, DataclassExecutionMetrics]:
        """Get all active metrics."""
        return self._metrics_buffer.copy()

    def get_metrics_summary(self, execution_id: str) -> dict[str, Any] | None:
        """Get a summary of metrics for an execution."""
        metrics = self._metrics_buffer.get(execution_id) or self._completed_metrics.get(
            execution_id
        )
        if not metrics:
            return None

        total_token_usage = {"input": 0, "output": 0, "total": 0}
        for node_metrics in metrics.node_metrics.values():
            if node_metrics.token_usage:
                total_token_usage["input"] += node_metrics.token_usage.get("input", 0)
                total_token_usage["output"] += node_metrics.token_usage.get("output", 0)
                total_token_usage["total"] += node_metrics.token_usage.get("total", 0)

        node_breakdown = []
        for node_id, node_metrics in metrics.node_metrics.items():
            node_data = {
                "node_id": node_id,
                "node_type": node_metrics.node_type,
                "duration_ms": node_metrics.duration_ms,
                "token_usage": node_metrics.token_usage or {"input": 0, "output": 0, "total": 0},
                "error": node_metrics.error,
                "module_timings": node_metrics.module_timings,
            }
            node_breakdown.append(node_data)

        bottlenecks = []
        for node_id in metrics.bottlenecks[:5]:
            if node_id in metrics.node_metrics:
                node_metrics = metrics.node_metrics[node_id]
                bottlenecks.append(
                    {
                        "node_id": node_id,
                        "node_type": node_metrics.node_type,
                        "duration_ms": node_metrics.duration_ms,
                    }
                )

        return {
            "execution_id": metrics.execution_id,
            "total_duration_ms": metrics.total_duration_ms,
            "node_count": len(metrics.node_metrics),
            "total_token_usage": total_token_usage,
            "bottlenecks": bottlenecks,
            "critical_path_length": len(metrics.critical_path),
            "parallelizable_groups": len(metrics.parallelizable_groups),
            "node_breakdown": node_breakdown,
        }

    async def start(self) -> None:
        """Start the metrics observer and cleanup loop."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.debug("MetricsObserver started")

    async def stop(self) -> None:
        """Stop the metrics observer and cleanup loop."""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        logger.info("MetricsObserver stopped")

    async def handle(self, event: DomainEvent) -> None:
        """Handle domain events (EventHandler protocol)."""
        await self.consume(event)

    async def consume(self, event: DomainEvent) -> None:
        """Process domain events related to execution metrics."""
        try:
            if event.type == EventType.EXECUTION_STARTED:
                await self._handle_execution_started(event)
            elif event.type == EventType.NODE_STARTED:
                await self._handle_node_started(event)
            elif event.type == EventType.NODE_COMPLETED:
                await self._handle_node_completed(event)
            elif event.type == EventType.NODE_ERROR:
                await self._handle_node_failed(event)
            elif event.type == EventType.EXECUTION_COMPLETED:
                await self._handle_execution_completed(event)
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)

    async def _handle_execution_started(self, event: DomainEvent) -> None:
        """Handle execution start event."""
        execution_id = event.scope.execution_id
        self._metrics_buffer[execution_id] = DataclassExecutionMetrics(
            execution_id=execution_id,
            start_time=event.occurred_at.timestamp(),
        )

    async def _handle_node_started(self, event: DomainEvent) -> None:
        """Handle node start event."""
        execution_id = event.scope.execution_id
        metrics = self._metrics_buffer.get(execution_id)
        if not metrics:
            return

        node_id = event.scope.node_id
        if not node_id:
            return

        payload = cast(NodeStartedPayload, event.payload)
        metrics.node_metrics[node_id] = DataclassNodeMetrics(
            node_id=node_id,
            node_type=payload.node_type or "unknown",
            start_time=event.occurred_at.timestamp(),
        )

        if payload.inputs and isinstance(payload.inputs, dict):
            deps = payload.inputs.get("dependencies", [])
            if deps:
                dependencies = self._analyzer._node_dependencies.get(execution_id, {})
                dependencies[node_id] = set(deps)
                self._analyzer.set_node_dependencies(execution_id, dependencies)

    async def _handle_node_completed(self, event: DomainEvent) -> None:
        """Handle node completion event."""
        execution_id = event.scope.execution_id
        metrics = self._metrics_buffer.get(execution_id)
        if not metrics:
            return

        node_id = event.scope.node_id
        if not node_id or node_id not in metrics.node_metrics:
            return

        node_metrics = metrics.node_metrics[node_id]
        node_metrics.end_time = event.occurred_at.timestamp()

        payload = cast(NodeCompletedPayload, event.payload)
        if payload.duration_ms:
            node_metrics.duration_ms = payload.duration_ms
        else:
            node_metrics.duration_ms = (node_metrics.end_time - node_metrics.start_time) * 1000

        if payload.token_usage:
            node_metrics.token_usage = payload.token_usage
            logger.debug(
                f"[MetricsObserver] Recorded token usage for {node_id}: {payload.token_usage}"
            )

    async def _handle_node_failed(self, event: DomainEvent) -> None:
        """Handle node failure event."""
        execution_id = event.scope.execution_id
        metrics = self._metrics_buffer.get(execution_id)
        if not metrics:
            return

        node_id = event.scope.node_id
        if not node_id or node_id not in metrics.node_metrics:
            return

        node_metrics = metrics.node_metrics[node_id]
        node_metrics.end_time = event.occurred_at.timestamp()
        node_metrics.duration_ms = (node_metrics.end_time - node_metrics.start_time) * 1000

        payload = cast(NodeErrorPayload, event.payload)
        node_metrics.error = payload.error_message

    def _convert_to_pydantic_metrics(
        self, dataclass_metrics: DataclassExecutionMetrics
    ) -> PydanticExecutionMetrics:
        """Convert dataclass ExecutionMetrics to Pydantic model for persistence."""
        # Convert node metrics
        pydantic_node_metrics = {}
        for node_id, node_metric in dataclass_metrics.node_metrics.items():
            pydantic_node_metrics[node_id] = PydanticNodeMetrics(
                node_id=node_metric.node_id,
                node_type=node_metric.node_type,
                start_time=node_metric.start_time,
                end_time=node_metric.end_time,
                duration_ms=node_metric.duration_ms,
                memory_usage=node_metric.memory_usage,
                llm_usage=node_metric.token_usage,
                error=node_metric.error,
                dependencies=list(node_metric.dependencies) if node_metric.dependencies else None,
                module_timings=node_metric.module_timings if node_metric.module_timings else None,
            )

        # Convert bottlenecks - use the analyzer's bottleneck data
        pydantic_bottlenecks = None
        if dataclass_metrics.bottlenecks:
            pydantic_bottlenecks = []
            for node_id in dataclass_metrics.bottlenecks:
                if node_id in dataclass_metrics.node_metrics:
                    node_metric = dataclass_metrics.node_metrics[node_id]
                    if node_metric.duration_ms and dataclass_metrics.total_duration_ms:
                        percentage = (
                            node_metric.duration_ms / dataclass_metrics.total_duration_ms
                        ) * 100
                        pydantic_bottlenecks.append(
                            Bottleneck(
                                node_id=node_id,
                                node_type=node_metric.node_type,
                                duration_ms=node_metric.duration_ms,
                                percentage=percentage,
                            )
                        )

        return PydanticExecutionMetrics(
            execution_id=dataclass_metrics.execution_id,
            start_time=dataclass_metrics.start_time,
            end_time=dataclass_metrics.end_time,
            total_duration_ms=dataclass_metrics.total_duration_ms,
            node_metrics=pydantic_node_metrics,
            critical_path=dataclass_metrics.critical_path
            if dataclass_metrics.critical_path
            else None,
            parallelizable_groups=(
                dataclass_metrics.parallelizable_groups
                if dataclass_metrics.parallelizable_groups
                else None
            ),
            bottlenecks=pydantic_bottlenecks,
        )

    async def _handle_execution_completed(self, event: DomainEvent) -> None:
        """Handle execution completion event."""
        execution_id = event.scope.execution_id
        logger.info(f"[MetricsObserver] Handling EXECUTION_COMPLETED for {execution_id}")
        metrics = self._metrics_buffer.get(execution_id)
        if not metrics:
            logger.warning(f"[MetricsObserver] No metrics found in buffer for {execution_id}")
            return
        logger.debug(f"[MetricsObserver] Found metrics in buffer for {execution_id}")

        metrics.end_time = event.occurred_at.timestamp()
        metrics.total_duration_ms = (metrics.end_time - metrics.start_time) * 1000

        await self._analyzer.analyze_execution(metrics, event.scope)

        # Retrieve timing data directly from collector (no file I/O!)
        timing_data = timing_collector.pop(execution_id)

        # Merge module timings into node metrics
        # Hierarchical phase names (e.g., "memory_selection__api_call") are preserved
        # to enable nested timing display in the CLI
        for node_id, phase_timings in timing_data.items():
            # Filter out metadata entries (end with "_metadata")
            # The hierarchical phase names themselves contain all needed info
            timings = {
                phase: dur_ms
                for phase, dur_ms in phase_timings.items()
                if not phase.endswith("_metadata")
            }

            if node_id in metrics.node_metrics:
                metrics.node_metrics[node_id].module_timings = timings
            else:
                # Create entry for system-level operations (scheduler, persistence, etc.)
                metrics.node_metrics[node_id] = DataclassNodeMetrics(
                    node_id=node_id,
                    node_type="system",
                    start_time=metrics.start_time,
                    end_time=metrics.end_time,
                    duration_ms=sum(timings.values()) if timings else 0,
                    module_timings=timings,
                )

        # Persist metrics to database if state_store is available
        if self.state_store:
            try:
                # Convert dataclass metrics to Pydantic model
                pydantic_metrics = self._convert_to_pydantic_metrics(metrics)

                # Get current execution state
                execution_state = await self.state_store.get_execution(execution_id)
                if execution_state:
                    # Create updated execution state with metrics (Pydantic models are immutable)
                    updated_state = execution_state.model_copy(update={"metrics": pydantic_metrics})

                    # Save to cache first
                    await self.state_store.save_execution(updated_state)

                    # Force immediate database persistence
                    if hasattr(self.state_store, "_persistence_manager") and hasattr(
                        self.state_store, "_cache_manager"
                    ):
                        # Get the cache entry
                        entry = await self.state_store._cache_manager.get_entry(execution_id)
                        if entry:
                            # Update the entry's state with metrics
                            entry.state = updated_state
                            entry.mark_dirty()
                            # Immediately persist to database
                            await self.state_store._persistence_manager.persist_entry(
                                execution_id, entry
                            )
                            logger.info(
                                f"Persisted metrics for execution {execution_id} to database (immediate)"
                            )
                    else:
                        logger.warning(
                            "State store doesn't support immediate persistence, metrics may not persist"
                        )
                else:
                    logger.warning(
                        f"Execution state not found for {execution_id}, cannot persist metrics"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to persist metrics for execution {execution_id}: {e}", exc_info=True
                )

        self._completed_metrics[execution_id] = metrics

        if len(self._completed_metrics) > self._max_completed_metrics:
            oldest_id = next(iter(self._completed_metrics))
            del self._completed_metrics[oldest_id]

        del self._metrics_buffer[execution_id]
        self._analyzer.clear_node_dependencies(execution_id)

    async def _cleanup_loop(self) -> None:
        """Periodically clean up stale metrics."""
        while self._running:
            try:
                await asyncio.sleep(300)

                current_time = time.time()
                stale_executions = []

                for exec_id, metrics in self._metrics_buffer.items():
                    if current_time - metrics.start_time > 3600:
                        stale_executions.append(exec_id)

                for exec_id in stale_executions:
                    logger.warning(f"Cleaning up stale metrics for execution {exec_id}")
                    del self._metrics_buffer[exec_id]
                    self._analyzer.clear_node_dependencies(exec_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
