"""Display and output formatting for CLI."""

from typing import Any

from dipeo.diagram_generated.enums import Status
from dipeo_server.cli.metrics_display import MetricsDisplayManager


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
        show_breakdown: bool = False,
        bottlenecks_only: bool = False,
        optimizations_only: bool = False,
    ) -> None:
        """Display metrics in human-readable format."""
        await MetricsDisplayManager.display_metrics(
            metrics, show_breakdown, bottlenecks_only, optimizations_only
        )
