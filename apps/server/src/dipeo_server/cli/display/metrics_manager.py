"""Metrics and statistics management for CLI."""

import json
from typing import Any

from dipeo.application.bootstrap import Container
from dipeo.application.registry.keys import STATE_STORE
from dipeo.config.base_logger import get_module_logger

from .display import DisplayManager

logger = get_module_logger(__name__)


class MetricsManager:
    """Manages metrics and statistics display for CLI commands."""

    def __init__(self, container: Container):
        """Initialize metrics manager.

        Args:
            container: Dependency injection container
        """
        self.container = container
        self.registry = container.registry
        self.display = DisplayManager()

    def _is_main_execution(self, execution_id: str) -> bool:
        """Check if execution ID is a main execution (not lightweight or sub-diagram).

        Filters out:
        - Lightweight executions (starting with "lightweight_")
        - Sub-diagram executions (containing "_sub_")

        Args:
            execution_id: The execution ID to check

        Returns:
            True if this is a main execution, False otherwise
        """
        exec_id_str = str(execution_id)
        return not (exec_id_str.startswith("lightweight_") or "_sub_" in exec_id_str)

    async def show_metrics(
        self,
        execution_id: str | None = None,
        latest: bool = False,
        diagram_id: str | None = None,
        breakdown: bool = False,
        bottlenecks_only: bool = False,
        optimizations_only: bool = False,
        output_json: bool = False,
    ) -> bool:
        """Display execution metrics from database (no server required).

        Args:
            execution_id: Specific execution ID to show metrics for
            latest: Show metrics for latest execution
            diagram_id: Filter by diagram ID
            breakdown: Show detailed breakdown
            bottlenecks_only: Show only bottlenecks
            optimizations_only: Show only optimization suggestions
            output_json: Output as JSON instead of formatted text

        Returns:
            True if metrics displayed successfully, False otherwise
        """
        try:
            state_store = self.registry.resolve(STATE_STORE)

            # Find the target execution
            target_execution_id = None
            if execution_id:
                target_execution_id = execution_id
            elif latest or diagram_id:
                # Fetch more executions to filter out lightweight/sub-diagram ones
                executions = await state_store.list_executions(diagram_id=diagram_id, limit=50)
                # Filter to main executions only
                main_executions = [e for e in executions if self._is_main_execution(e.id)]
                if main_executions:
                    target_execution_id = main_executions[0].id
                else:
                    if diagram_id:
                        print(f"No main executions found for diagram: {diagram_id}")
                    else:
                        print("No main executions found")
                    return False
            else:
                # Fetch more executions to filter out lightweight/sub-diagram ones
                executions = await state_store.list_executions(limit=50)
                # Filter to main executions only
                main_executions = [e for e in executions if self._is_main_execution(e.id)]
                if main_executions:
                    target_execution_id = main_executions[0].id
                else:
                    print("No main executions found")
                    return False

            # Get execution state from database
            execution_state = await state_store.get_execution(str(target_execution_id))
            if not execution_state:
                print(f"❌ Execution {target_execution_id} not found")
                return False

            # Check if metrics are available
            if not execution_state.metrics:
                print(f"❌ No metrics available for execution {target_execution_id}")
                print(
                    "   Metrics are only available for executions run with --timing or --debug flags"
                )
                return False

            # Convert Pydantic metrics to summary dict format
            metrics_data = execution_state.metrics
            total_token_usage = {"input": 0, "output": 0, "total": 0}

            node_breakdown = []
            for node_id, node_metrics in metrics_data.node_metrics.items():
                # Accumulate token usage (llm_usage is a Pydantic model, not a dict)
                if node_metrics.llm_usage:
                    total_token_usage["input"] += node_metrics.llm_usage.input or 0
                    total_token_usage["output"] += node_metrics.llm_usage.output or 0
                    total_token_usage["total"] += node_metrics.llm_usage.total or 0

                # Convert llm_usage Pydantic model to dict
                token_usage_dict = {"input": 0, "output": 0, "total": 0}
                if node_metrics.llm_usage:
                    token_usage_dict = {
                        "input": node_metrics.llm_usage.input or 0,
                        "output": node_metrics.llm_usage.output or 0,
                        "total": node_metrics.llm_usage.total or 0,
                    }

                node_breakdown.append(
                    {
                        "node_id": node_id,
                        "node_type": node_metrics.node_type,
                        "duration_ms": node_metrics.duration_ms,
                        "token_usage": token_usage_dict,
                        "error": node_metrics.error,
                        "module_timings": node_metrics.module_timings or {},
                    }
                )

            bottlenecks = []
            if metrics_data.bottlenecks:
                for bottleneck in metrics_data.bottlenecks[:5]:
                    bottlenecks.append(
                        {
                            "node_id": bottleneck.node_id,
                            "node_type": bottleneck.node_type,
                            "duration_ms": bottleneck.duration_ms,
                        }
                    )

            metrics_summary = {
                "execution_id": str(metrics_data.execution_id),
                "total_duration_ms": metrics_data.total_duration_ms,
                "node_count": len(metrics_data.node_metrics),
                "total_token_usage": total_token_usage,
                "bottlenecks": bottlenecks,
                "critical_path_length": len(metrics_data.critical_path)
                if metrics_data.critical_path
                else 0,
                "parallelizable_groups": len(metrics_data.parallelizable_groups)
                if metrics_data.parallelizable_groups
                else 0,
                "node_breakdown": node_breakdown,
            }

            if output_json:
                print(json.dumps(metrics_summary, indent=2, default=str))
            else:
                await self.display.display_metrics(
                    metrics_summary, breakdown, bottlenecks_only, optimizations_only
                )

            return True

        except Exception as e:
            logger.error(f"Failed to display metrics: {e}", exc_info=True)
            return False

    async def show_stats(self, diagram_path: str) -> bool:
        """Show diagram statistics.

        Args:
            diagram_path: Path to the diagram file

        Returns:
            True if stats displayed successfully, False otherwise
        """
        try:
            from ..core.diagram_loader import DiagramLoader

            loader = DiagramLoader()
            diagram_data, _ = await loader.load_diagram(diagram_path, None)

            node_count = len(diagram_data.get("nodes", []))
            edge_count = len(diagram_data.get("edges", []))

            print(f"\n📊 Diagram Statistics: {diagram_path}")
            print(f"  Nodes: {node_count}")
            print(f"  Edges: {edge_count}")

            node_types = {}
            for node in diagram_data.get("nodes", []):
                node_type = node.get("type", "unknown")
                node_types[node_type] = node_types.get(node_type, 0) + 1

            print("\n  Node Types:")
            for node_type, count in sorted(node_types.items()):
                print(f"    {node_type}: {count}")

            return True

        except Exception as e:
            logger.error(f"Failed to show stats: {e}")
            return False
