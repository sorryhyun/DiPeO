"""Metrics command for displaying execution metrics."""

import json
import traceback

import requests

from ..server_manager import ServerManager
from ..graphql_queries import GraphQLQueries


class MetricsCommand:
    """Command for displaying execution metrics."""

    def __init__(self, server: ServerManager):
        self.server = server

    def execute(
        self,
        execution_id: str | None = None,
        diagram_id: str | None = None,
        bottlenecks_only: bool = False,
        optimizations_only: bool = False,
        output_json: bool = False,
    ):
        """Display execution metrics."""
        # Ensure server is running
        if not self.server.is_running() and not self.server.start():
            print("❌ Failed to start server")
            return

        try:
            # GraphQL endpoint
            url = "http://localhost:8000/graphql"

            if execution_id:
                self._query_execution_metrics(
                    url, execution_id, output_json, bottlenecks_only, optimizations_only
                )
            elif diagram_id:
                self._query_diagram_history(
                    url, diagram_id, output_json, bottlenecks_only, optimizations_only
                )
            else:
                self._query_latest_execution(
                    url, output_json, bottlenecks_only, optimizations_only
                )

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch metrics: {e}")
        except Exception as e:
            print(f"❌ Error displaying metrics: {e}")
            traceback.print_exc()

    def _query_execution_metrics(
        self, url: str, execution_id: str, output_json: bool, bottlenecks_only: bool, optimizations_only: bool
    ):
        """Query specific execution metrics."""
        query = GraphQLQueries.EXECUTION_METRICS_DETAILED
        variables = {"executionId": execution_id}

        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            print(f"❌ GraphQL errors: {result['errors']}")
            return

        execution = result.get("data", {}).get("execution")
        if not execution:
            print(f"❌ Execution {execution_id} not found")
            return

        metrics = execution.get("metrics")
        if not metrics:
            print(f"⚠️ No metrics available for execution {execution_id}")
            return

        if output_json:
            print(json.dumps(metrics, indent=2))
        else:
            self._display_metrics(execution, metrics, bottlenecks_only, optimizations_only)

    def _query_diagram_history(
        self, url: str, diagram_id: str, output_json: bool, bottlenecks_only: bool, optimizations_only: bool
    ):
        """Query execution history for diagram."""
        query = GraphQLQueries.EXECUTION_HISTORY
        variables = {
            "diagramId": diagram_id,
            "includeMetrics": True
        }

        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            print(f"❌ GraphQL errors: {result['errors']}")
            return

        executions = result.get("data", {}).get("executionHistory", [])
        if not executions:
            print(f"⚠️ No executions found for diagram {diagram_id}")
            return

        if output_json:
            print(json.dumps(executions, indent=2))
        else:
            self._display_history_metrics(executions, bottlenecks_only, optimizations_only)

    def _query_latest_execution(
        self, url: str, output_json: bool, bottlenecks_only: bool, optimizations_only: bool
    ):
        """Query latest execution."""
        query = GraphQLQueries.LATEST_EXECUTION

        response = requests.post(
            url,
            json={"query": query},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            print(f"❌ GraphQL errors: {result['errors']}")
            return

        executions = result.get("data", {}).get("executions", [])
        if not executions:
            print("⚠️ No executions found")
            return

        execution = executions[0]
        metrics = execution.get("metrics")

        if not metrics:
            print("⚠️ No metrics available for latest execution")
            return

        if output_json:
            print(json.dumps(metrics, indent=2))
        else:
            self._display_metrics(execution, metrics, bottlenecks_only, optimizations_only)

    def _display_metrics(self, execution, metrics, bottlenecks_only, optimizations_only):
        """Display formatted metrics for a single execution."""
        print("\n📊 Execution Metrics")
        print("=" * 60)
        print(f"Execution ID: {execution['id']}")
        print(f"Diagram ID: {execution.get('diagramId', 'N/A')}")
        print(f"Status: {execution['status']}")
        print(f"Duration: {execution.get('durationSeconds', 0):.2f}s")

        if not bottlenecks_only and not optimizations_only:
            # Show general metrics
            print("\n⏱️ Performance Summary:")
            print(f"  Total Duration: {metrics.get('total_duration_ms', 0):.0f}ms")
            print(f"  Node Count: {len(metrics.get('node_metrics', {}))}")

            # Show critical path
            critical_path = metrics.get('critical_path', [])
            if critical_path:
                print(f"\n🛤️ Critical Path ({len(critical_path)} nodes):")
                for node_id in critical_path[:5]:  # Show top 5
                    node_metric = metrics.get('node_metrics', {}).get(node_id, {})
                    duration = node_metric.get('duration_ms', 0)
                    node_type = node_metric.get('node_type', 'unknown')
                    print(f"  • {node_id} ({node_type}): {duration:.0f}ms")

        # Show bottlenecks
        if not optimizations_only:
            bottlenecks = metrics.get('bottlenecks', [])
            if bottlenecks:
                print(f"\n🔥 Bottlenecks ({len(bottlenecks)} nodes):")
                for node_id in bottlenecks[:5]:  # Show top 5
                    node_metric = metrics.get('node_metrics', {}).get(node_id, {})
                    duration = node_metric.get('duration_ms', 0)
                    node_type = node_metric.get('node_type', 'unknown')
                    print(f"  • {node_id} ({node_type}): {duration:.0f}ms")

        # Show parallelizable groups
        if not bottlenecks_only:
            parallelizable = metrics.get('parallelizable_groups', [])
            if parallelizable:
                print(f"\n⚡ Parallelizable Groups ({len(parallelizable)} groups):")
                for i, group in enumerate(parallelizable[:3], 1):  # Show top 3
                    print(f"  Group {i}: {', '.join(group)}")

    def _display_history_metrics(self, executions, bottlenecks_only, optimizations_only):
        """Display metrics history for multiple executions."""
        print("\n📈 Execution History Metrics")
        print("=" * 60)

        for execution in executions:
            print(f"\n▶ Execution {execution['id']}")
            print(f"  Status: {execution['status']}")
            print(f"  Started: {execution.get('startedAt', 'N/A')}")
            print(f"  Duration: {execution.get('durationSeconds', 0):.2f}s")

            metrics = execution.get('metrics')
            if metrics:
                if not optimizations_only:
                    bottlenecks = metrics.get('bottlenecks', [])
                    if bottlenecks:
                        print(f"  Bottlenecks: {len(bottlenecks)} nodes")

                if not bottlenecks_only:
                    parallelizable = metrics.get('parallelizable_groups', [])
                    if parallelizable:
                        print(f"  Parallelizable: {len(parallelizable)} groups")
            else:
                print("  No metrics available")
