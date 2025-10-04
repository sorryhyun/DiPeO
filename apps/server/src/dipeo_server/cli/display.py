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
        show_breakdown: bool = False,
        bottlenecks_only: bool = False,
        optimizations_only: bool = False,
    ) -> None:
        """Display metrics in human-readable format."""
        total_duration = metrics.get("total_duration_ms", 0)
        node_count = metrics.get("node_count", 0)
        node_breakdown = metrics.get("node_breakdown", [])

        print("\n📊 Execution Metrics")
        print(f"  Execution ID: {metrics.get('execution_id')}")
        print(f"  Total Duration: {total_duration:.0f}ms ({total_duration/1000:.2f}s)")
        print(f"  Nodes Executed: {node_count}")
        if node_count > 0:
            avg_duration = total_duration / node_count
            print(f"  Avg Node Duration: {avg_duration:.0f}ms")

        # Token usage summary
        total_tokens = metrics.get("total_token_usage", {})
        if total_tokens and total_tokens.get("total", 0) > 0:
            print("\n🪙 Token Usage:")
            print(f"  Input:  {total_tokens.get('input', 0):,} tokens")
            print(f"  Output: {total_tokens.get('output', 0):,} tokens")
            print(f"  Total:  {total_tokens.get('total', 0):,} tokens")

        # Bottlenecks (show by default unless optimizations_only)
        if not optimizations_only:
            bottlenecks = metrics.get("bottlenecks", [])
            if bottlenecks:
                print("\n⚠️  Top Bottlenecks:")
                for i, bottleneck in enumerate(bottlenecks[:5], 1):
                    if isinstance(bottleneck, dict):
                        node_id = bottleneck.get("node_id", "unknown")
                        node_type = bottleneck.get("node_type", "unknown")
                        duration = bottleneck.get("duration_ms", 0)
                        pct = (duration / total_duration * 100) if total_duration > 0 else 0
                        print(
                            f"  {i}. {node_id} ({node_type}): {duration:.0f}ms ({pct:.1f}% of total)"
                        )
                    else:
                        print(f"  {i}. {bottleneck}")

        # Module-level breakdown
        if show_breakdown and node_breakdown:
            # Collect all phases across all nodes
            all_phases = {}
            for node_data in node_breakdown:
                module_timings = node_data.get("module_timings", {})
                for phase, duration in module_timings.items():
                    if phase not in all_phases:
                        all_phases[phase] = []
                    all_phases[phase].append(duration)

            if all_phases:
                print("\n⏱️  Phase Timing Summary:")
                # Calculate stats for each phase
                phase_stats = []
                for phase, durations in all_phases.items():
                    total = sum(durations)
                    avg = total / len(durations)
                    max_dur = max(durations)
                    count = len(durations)
                    phase_stats.append(
                        {"phase": phase, "total": total, "avg": avg, "max": max_dur, "count": count}
                    )

                # Sort by total time
                phase_stats.sort(key=lambda x: x["total"], reverse=True)

                for stat in phase_stats[:10]:  # Top 10 phases
                    pct = (stat["total"] / total_duration * 100) if total_duration > 0 else 0
                    print(
                        f"  {stat['phase']:30s} Total: {stat['total']:7.0f}ms ({pct:5.1f}%) "
                        f"Avg: {stat['avg']:6.0f}ms Max: {stat['max']:6.0f}ms Count: {stat['count']}"
                    )

            print("\n⏱️  Per-Node Timing Breakdown:")
            for node_data in node_breakdown:
                node_id = node_data["node_id"]
                node_type = node_data.get("node_type", "unknown")
                total_ms = node_data.get("duration_ms", 0)
                module_timings = node_data.get("module_timings", {})
                token_usage = node_data.get("token_usage", {})

                if not module_timings:
                    continue

                pct_of_total = (total_ms / total_duration * 100) if total_duration > 0 else 0
                token_str = ""
                if token_usage and token_usage.get("total", 0) > 0:
                    token_str = f" | Tokens: {token_usage.get('total', 0):,}"

                print(
                    f"\n  {node_id} ({node_type}) - {total_ms:.0f}ms ({pct_of_total:.1f}%){token_str}"
                )

                # Sort by duration descending
                sorted_phases = sorted(module_timings.items(), key=lambda x: x[1], reverse=True)

                for phase, duration in sorted_phases:
                    pct = (duration / total_ms * 100) if total_ms > 0 else 0
                    print(f"    ├─ {phase:30s} {duration:7.0f}ms ({pct:5.1f}%)")

        if optimizations_only:
            optimizations = metrics.get("optimization_suggestions", [])
            if optimizations:
                print("\n💡 Optimization Suggestions:")
                for suggestion in optimizations:
                    print(f"  - {suggestion}")
            else:
                print("\n💡 No optimization suggestions available")
