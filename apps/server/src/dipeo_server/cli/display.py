"""Display and output formatting for CLI."""

from typing import Any

from dipeo.diagram_generated.enums import Status


class DisplayManager:
    """Handles various output display formats."""

    @staticmethod
    async def display_rich_results(result: Any, success: bool = False) -> None:
        """Display results using rich formatting."""
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table

            console = Console()

            if success or (result and result.status == Status.COMPLETED):
                console.print(Panel.fit("✅ Execution Successful", style="green bold"))
            else:
                console.print(Panel.fit("❌ Execution Failed", style="red bold"))

            if hasattr(result, "node_outputs") and result.node_outputs:
                table = Table(title="Outputs")
                table.add_column("Node", style="cyan")
                table.add_column("Output", style="white")

                for node_id, output in result.node_outputs.items():
                    table.add_row(node_id, str(output)[:100])

                console.print(table)

        except ImportError:
            await DisplayManager.display_simple_results(result, success)

    @staticmethod
    async def display_simple_results(result: Any, success: bool = False) -> None:
        """Display results using simple text formatting."""
        if success or (result and result.status == Status.COMPLETED):
            print("✅ Execution Successful")
        else:
            print("❌ Execution Failed")

        if hasattr(result, "node_outputs") and result.node_outputs:
            print("\nOutputs:")
            for node_id, output in result.node_outputs.items():
                print(f"  {node_id}: {str(output)[:100]}")

    @staticmethod
    async def display_metrics(
        metrics: dict[str, Any],
        bottlenecks_only: bool,
        optimizations_only: bool,
    ) -> None:
        """Display metrics in human-readable format."""
        print("\n📊 Execution Metrics")
        print(f"  Execution ID: {metrics.get('execution_id')}")
        print(f"  Total Duration: {metrics.get('total_duration_ms', 0):.2f}ms")
        print(f"  Nodes Executed: {metrics.get('nodes_executed', 0)}")

        if bottlenecks_only or not optimizations_only:
            bottlenecks = metrics.get("bottlenecks", [])
            if bottlenecks:
                print("\n⚠️ Bottlenecks:")
                for bottleneck in bottlenecks:
                    print(f"  - {bottleneck}")

        if optimizations_only or not bottlenecks_only:
            optimizations = metrics.get("optimization_suggestions", [])
            if optimizations:
                print("\n💡 Optimization Suggestions:")
                for suggestion in optimizations:
                    print(f"  - {suggestion}")
