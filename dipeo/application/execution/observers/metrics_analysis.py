"""Metrics analysis and optimization logic."""

from typing import Any

from dipeo.application.execution.observers.metrics_types import ExecutionMetrics
from dipeo.config.base_logger import get_module_logger
from dipeo.domain.events import DomainEvent, EventBus, EventScope, EventType, ExecutionLogPayload

logger = get_module_logger(__name__)


class MetricsAnalyzer:
    """Analyzes execution metrics and provides optimization suggestions."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        analysis_threshold_ms: float = 1000,
    ):
        self.event_bus = event_bus
        self.analysis_threshold_ms = analysis_threshold_ms
        self._node_dependencies: dict[str, dict[str, set[str]]] = {}

    def set_node_dependencies(self, execution_id: str, dependencies: dict[str, set[str]]) -> None:
        """Set dependency information for an execution."""
        self._node_dependencies[execution_id] = dependencies

    def clear_node_dependencies(self, execution_id: str) -> None:
        """Clear dependency information for an execution."""
        if execution_id in self._node_dependencies:
            del self._node_dependencies[execution_id]

    async def analyze_execution(self, metrics: ExecutionMetrics, scope: EventScope) -> None:
        """Analyze completed execution and emit optimization suggestions."""
        bottlenecks = self._identify_bottlenecks(metrics)
        metrics.bottlenecks = [b["node_id"] for b in bottlenecks[:5]]
        metrics.critical_path = self._calculate_critical_path(metrics)
        metrics.parallelizable_groups = self._find_parallelizable_nodes(metrics)

        if self.event_bus:
            await self._emit_metrics_event(metrics, scope, bottlenecks)
            await self._emit_optimization_suggestions(metrics, scope)

    async def _emit_metrics_event(
        self, metrics: ExecutionMetrics, scope: EventScope, bottlenecks: list[dict[str, Any]]
    ) -> None:
        """Emit comprehensive metrics as an event."""
        node_breakdown = []
        total_token_usage = {"input": 0, "output": 0, "total": 0}
        for node_id, node_metrics in metrics.node_metrics.items():
            node_data = {
                "node_id": node_id,
                "node_type": node_metrics.node_type,
                "duration_ms": node_metrics.duration_ms,
                "token_usage": node_metrics.token_usage or {"input": 0, "output": 0, "total": 0},
                "error": node_metrics.error,
            }
            node_breakdown.append(node_data)

            if node_metrics.token_usage:
                total_token_usage["input"] += node_metrics.token_usage.get("input", 0)
                total_token_usage["output"] += node_metrics.token_usage.get("output", 0)
                total_token_usage["total"] += node_metrics.token_usage.get("total", 0)

        metrics_dict = {
            "execution_id": metrics.execution_id,
            "total_duration_ms": metrics.total_duration_ms,
            "node_count": len(metrics.node_metrics),
            "total_token_usage": total_token_usage,
            "bottlenecks": bottlenecks[:5],
            "critical_path_length": len(metrics.critical_path),
            "parallelizable_groups": len(metrics.parallelizable_groups),
            "node_breakdown": node_breakdown,
        }

        await self.event_bus.publish(
            DomainEvent(
                type=EventType.EXECUTION_LOG,
                scope=scope,
                payload=ExecutionLogPayload(
                    level="INFO",
                    message="Execution metrics collected",
                    logger_name="metrics_observer",
                    extra_fields=metrics_dict,
                ),
            )
        )

    async def _emit_optimization_suggestions(
        self, metrics: ExecutionMetrics, scope: EventScope
    ) -> None:
        """Emit optimization suggestions if improvements are possible."""
        if metrics.parallelizable_groups:
            potential_savings = self._estimate_parallel_savings(metrics)
            await self.event_bus.publish(
                DomainEvent(
                    type=EventType.EXECUTION_LOG,
                    scope=scope,
                    payload=ExecutionLogPayload(
                        level="INFO",
                        message=f"Found {len(metrics.parallelizable_groups)} groups of nodes that could run in parallel. Could save up to {potential_savings}ms",
                        logger_name="metrics_observer",
                        extra_fields={
                            "suggestion_type": "parallelize_nodes",
                            "affected_nodes": [
                                n for group in metrics.parallelizable_groups for n in group
                            ],
                            "parallelizable_groups": metrics.parallelizable_groups,
                        },
                    ),
                )
            )

    def _identify_bottlenecks(self, metrics: ExecutionMetrics) -> list[dict[str, Any]]:
        """Identify nodes that exceed the analysis threshold."""
        bottlenecks = []
        for node_id, node_metrics in metrics.node_metrics.items():
            if node_metrics.duration_ms and node_metrics.duration_ms > self.analysis_threshold_ms:
                bottlenecks.append(
                    {
                        "node_id": node_id,
                        "node_type": node_metrics.node_type,
                        "duration_ms": node_metrics.duration_ms,
                    }
                )
        bottlenecks.sort(key=lambda x: x["duration_ms"], reverse=True)
        return bottlenecks

    def _calculate_critical_path(self, metrics: ExecutionMetrics) -> list[str]:
        """Calculate the critical execution path based on start times."""
        sorted_nodes = sorted(metrics.node_metrics.items(), key=lambda x: x[1].start_time)
        return [node_id for node_id, _ in sorted_nodes]

    def _find_parallelizable_nodes(self, metrics: ExecutionMetrics) -> list[list[str]]:
        """Find groups of nodes that could be executed in parallel."""
        groups = []
        exec_id = metrics.execution_id

        if exec_id not in self._node_dependencies:
            return groups

        dependencies = self._node_dependencies[exec_id]
        potential_group = []

        for node_id in metrics.node_metrics:
            node_deps = dependencies.get(node_id, set())
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
                savings = sum(durations) - max(durations)
                total_savings += savings

        return total_savings
