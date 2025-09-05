"""Metrics collection observer for execution analysis and optimization."""

import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, cast

from dipeo.domain.events import (
    DomainEvent,
    EventBus,
    EventScope,
    EventType,
    MetricsCollectedPayload,
    NodeCompletedPayload,
    NodeErrorPayload,
    NodeStartedPayload,
    OptimizationSuggestedPayload,
)

logger = logging.getLogger(__name__)


@dataclass
class NodeMetrics:
    """Metrics for a single node execution."""

    node_id: str
    node_type: str
    start_time: float
    end_time: float | None = None
    duration_ms: float | None = None
    memory_usage: int | None = None
    token_usage: dict[str, int] | None = None
    error: str | None = None
    dependencies: set[str] = field(default_factory=set)


@dataclass
class ExecutionMetrics:
    """Aggregated metrics for an entire execution."""

    execution_id: str
    start_time: float
    end_time: float | None = None
    total_duration_ms: float | None = None
    node_metrics: dict[str, NodeMetrics] = field(default_factory=dict)
    critical_path: list[str] = field(default_factory=list)
    parallelizable_groups: list[list[str]] = field(default_factory=list)
    bottlenecks: list[str] = field(default_factory=list)


@dataclass
class DiagramOptimization:
    """Optimization suggestions for a diagram."""

    execution_id: str
    diagram_id: str | None
    bottlenecks: list[dict[str, Any]]
    parallelizable: list[list[str]]
    suggested_changes: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "diagram_id": self.diagram_id,
            "bottlenecks": self.bottlenecks,
            "parallelizable": self.parallelizable,
            "suggested_changes": self.suggested_changes,
        }


class MetricsObserver(EventBus):
    """Collects execution metrics for analysis and optimization suggestions.

    This observer:
    - Tracks execution performance metrics
    - Identifies bottlenecks and optimization opportunities
    - Emits suggestions for diagram improvements
    - Provides foundation for self-modifying diagrams
    """

    def __init__(self, event_bus: EventBus | None = None):
        self._metrics_buffer: dict[str, ExecutionMetrics] = {}
        self._node_dependencies: dict[str, dict[str, set[str]]] = {}  # exec_id -> node_id -> deps
        self.event_bus = event_bus
        self._analysis_threshold_ms = 1000  # Nodes taking > 1s are potential bottlenecks
        self._cleanup_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the metrics observer."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.debug("MetricsObserver started")

    async def stop(self) -> None:
        """Stop the metrics observer."""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        logger.info("MetricsObserver stopped")

    async def consume(self, event: DomainEvent) -> None:
        """Process execution events to collect metrics."""
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
        """Initialize metrics for a new execution."""
        execution_id = event.scope.execution_id
        self._metrics_buffer[execution_id] = ExecutionMetrics(
            execution_id=execution_id,
            start_time=event.occurred_at.timestamp(),
        )
        self._node_dependencies[execution_id] = {}

    async def _handle_node_started(self, event: DomainEvent) -> None:
        """Track node start time."""
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

        # Track dependencies from inputs if available
        if payload.inputs and isinstance(payload.inputs, dict):
            deps = payload.inputs.get("dependencies", [])
            if deps:
                self._node_dependencies[execution_id][node_id] = set(deps)

    async def _handle_node_completed(self, event: DomainEvent) -> None:
        """Track node completion and calculate duration."""
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

    async def _handle_node_failed(self, event: DomainEvent) -> None:
        """Track node failures."""
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
        """Finalize metrics and emit analysis events."""
        execution_id = event.scope.execution_id
        metrics = self._metrics_buffer.get(execution_id)
        if not metrics:
            return

        metrics.end_time = event.occurred_at.timestamp()
        metrics.total_duration_ms = (metrics.end_time - metrics.start_time) * 1000

        # Analyze and emit metrics
        await self._analyze_execution(metrics, event.scope)

        # Clean up
        del self._metrics_buffer[execution_id]
        if execution_id in self._node_dependencies:
            del self._node_dependencies[execution_id]

    async def _analyze_execution(self, metrics: ExecutionMetrics, scope: EventScope) -> None:
        """Analyze execution metrics and emit findings."""
        # Identify bottlenecks (slowest nodes)
        bottlenecks = []
        for node_id, node_metrics in metrics.node_metrics.items():
            if node_metrics.duration_ms and node_metrics.duration_ms > self._analysis_threshold_ms:
                bottlenecks.append(
                    {
                        "node_id": node_id,
                        "node_type": node_metrics.node_type,
                        "duration_ms": node_metrics.duration_ms,
                    }
                )

        # Sort by duration
        bottlenecks.sort(key=lambda x: x["duration_ms"], reverse=True)
        metrics.bottlenecks = [b["node_id"] for b in bottlenecks[:5]]  # Top 5 slowest

        # Calculate critical path (simplified - just longest sequential chain)
        metrics.critical_path = self._calculate_critical_path(metrics)

        # Identify parallelizable groups
        metrics.parallelizable_groups = self._find_parallelizable_nodes(metrics)

        # Emit metrics event
        if self.event_bus:
            metrics_dict = {
                "execution_id": metrics.execution_id,
                "total_duration_ms": metrics.total_duration_ms,
                "node_count": len(metrics.node_metrics),
                "bottlenecks": bottlenecks[:5],
                "critical_path_length": len(metrics.critical_path),
                "parallelizable_groups": len(metrics.parallelizable_groups),
            }

            await self.event_bus.publish(
                DomainEvent(
                    type=EventType.METRICS_COLLECTED,
                    scope=scope,
                    payload=MetricsCollectedPayload(metrics=metrics_dict),
                )
            )

            # Emit optimization suggestions if there are improvements
            if metrics.parallelizable_groups:
                await self.event_bus.publish(
                    DomainEvent(
                        type=EventType.OPTIMIZATION_SUGGESTED,
                        scope=scope,
                        payload=OptimizationSuggestedPayload(
                            suggestion_type="parallelize_nodes",
                            affected_nodes=[
                                n for group in metrics.parallelizable_groups for n in group
                            ],
                            expected_improvement=f"Could save up to {self._estimate_parallel_savings(metrics)}ms",
                            description=f"Found {len(metrics.parallelizable_groups)} groups of nodes that could run in parallel",
                        ),
                    )
                )

    def _calculate_critical_path(self, metrics: ExecutionMetrics) -> list[str]:
        """Calculate the critical path through the execution."""
        # Simplified: return nodes in execution order that took the longest
        sorted_nodes = sorted(metrics.node_metrics.items(), key=lambda x: x[1].start_time)
        return [node_id for node_id, _ in sorted_nodes]

    def _find_parallelizable_nodes(self, metrics: ExecutionMetrics) -> list[list[str]]:
        """Find groups of nodes that could run in parallel."""
        groups = []
        exec_id = metrics.execution_id

        if exec_id not in self._node_dependencies:
            return groups

        dependencies = self._node_dependencies[exec_id]

        # Find nodes with no dependencies on each other
        potential_group = []
        for node_id in metrics.node_metrics:
            node_deps = dependencies.get(node_id, set())

            # Check if this node can run in parallel with nodes in potential_group
            can_parallel = True
            for other_id in potential_group:
                other_deps = dependencies.get(other_id, set())
                if node_id in other_deps or other_id in node_deps:
                    can_parallel = False
                    break

            if can_parallel:
                potential_group.append(node_id)
            elif len(potential_group) > 1:
                groups.append(potential_group)
                potential_group = [node_id]

        if len(potential_group) > 1:
            groups.append(potential_group)

        return groups

    def _estimate_parallel_savings(self, metrics: ExecutionMetrics) -> float:
        """Estimate time savings from parallelization."""
        total_savings = 0.0

        for group in metrics.parallelizable_groups:
            durations = []
            for node_id in group:
                if node_id in metrics.node_metrics:
                    duration = metrics.node_metrics[node_id].duration_ms
                    if duration:
                        durations.append(duration)

            if durations:
                # Savings = sum of all durations - max duration (parallel execution time)
                savings = sum(durations) - max(durations)
                total_savings += savings

        return total_savings

    async def _cleanup_loop(self) -> None:
        """Periodically clean up stale metrics."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes

                current_time = time.time()
                stale_executions = []

                for exec_id, metrics in self._metrics_buffer.items():
                    # Remove metrics older than 1 hour without completion
                    if current_time - metrics.start_time > 3600:
                        stale_executions.append(exec_id)

                for exec_id in stale_executions:
                    logger.warning(f"Cleaning up stale metrics for execution {exec_id}")
                    del self._metrics_buffer[exec_id]
                    if exec_id in self._node_dependencies:
                        del self._node_dependencies[exec_id]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
