"""Metrics collection observer for execution analysis."""

import asyncio
import contextlib
import logging
import time
from typing import Any, cast

from dipeo.application.execution.observers.metrics_analysis import MetricsAnalyzer
from dipeo.application.execution.observers.metrics_types import ExecutionMetrics, NodeMetrics
from dipeo.config.base_logger import get_module_logger
from dipeo.domain.events import (
    DomainEvent,
    EventBus,
    EventType,
    NodeCompletedPayload,
    NodeErrorPayload,
    NodeStartedPayload,
)

logger = get_module_logger(__name__)


class MetricsObserver(EventBus):
    """Collects execution metrics for analysis and optimization suggestions."""

    def __init__(self, event_bus: EventBus | None = None):
        self._metrics_buffer: dict[str, ExecutionMetrics] = {}
        self._completed_metrics: dict[str, ExecutionMetrics] = {}
        self.event_bus = event_bus
        self._cleanup_task: asyncio.Task | None = None
        self._running = False
        self._max_completed_metrics = 10

        self._analyzer = MetricsAnalyzer(event_bus=event_bus, analysis_threshold_ms=1000)

    def get_execution_metrics(self, execution_id: str) -> ExecutionMetrics | None:
        """Get metrics for a specific execution."""
        return self._metrics_buffer.get(execution_id) or self._completed_metrics.get(execution_id)

    def get_all_metrics(self) -> dict[str, ExecutionMetrics]:
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
        self._metrics_buffer[execution_id] = ExecutionMetrics(
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
        metrics.node_metrics[node_id] = NodeMetrics(
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

    async def _handle_execution_completed(self, event: DomainEvent) -> None:
        """Handle execution completion event."""
        execution_id = event.scope.execution_id
        metrics = self._metrics_buffer.get(execution_id)
        if not metrics:
            return

        metrics.end_time = event.occurred_at.timestamp()
        metrics.total_duration_ms = (metrics.end_time - metrics.start_time) * 1000

        await self._analyzer.analyze_execution(metrics, event.scope)
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
