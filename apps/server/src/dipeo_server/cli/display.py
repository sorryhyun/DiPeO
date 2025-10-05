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
            # Collect system-level and node-level phases separately
            system_phases = {}
            node_phases = {}

            for node_data in node_breakdown:
                module_timings = node_data.get("module_timings", {})
                node_id = node_data.get("node_id", "")

                for phase, duration in module_timings.items():
                    # System operations have node_id = "system"
                    if node_id == "system":
                        if phase not in system_phases:
                            system_phases[phase] = []
                        system_phases[phase].append(duration)
                    else:
                        if phase not in node_phases:
                            node_phases[phase] = []
                        node_phases[phase].append(duration)

            # Show system-level operations first
            if system_phases:
                print("\n🔧 System Operations Timing:")
                system_stats = []
                for phase, durations in system_phases.items():
                    total = sum(durations)
                    avg = total / len(durations)
                    max_dur = max(durations)
                    count = len(durations)
                    system_stats.append(
                        {"phase": phase, "total": total, "avg": avg, "max": max_dur, "count": count}
                    )

                system_stats.sort(key=lambda x: x["total"], reverse=True)

                for stat in system_stats:
                    pct = (stat["total"] / total_duration * 100) if total_duration > 0 else 0
                    print(
                        f"  {stat['phase']:30s} Total: {int(stat['total']):7d}ms ({pct:5.1f}%) "
                        f"Avg: {int(stat['avg']):6d}ms Max: {int(stat['max']):6d}ms Count: {stat['count']}"
                    )

            # Show node-level phases with hierarchical structure
            if node_phases:
                print("\n⏱️  Node Phase Timing Summary:")

                # Parse hierarchical phases
                hierarchical_stats = {}
                flat_stats = {}

                for phase, durations in node_phases.items():
                    total = sum(durations)
                    avg = total / len(durations)
                    max_dur = max(durations)
                    count = len(durations)

                    # Check if this is a hierarchical phase (contains __)
                    if "__" in phase:
                        parent, child = phase.split("__", 1)

                        # Track parent phase
                        if parent not in hierarchical_stats:
                            hierarchical_stats[parent] = {
                                "total": 0,
                                "count": 0,
                                "children": {}
                            }
                        hierarchical_stats[parent]["total"] += total
                        hierarchical_stats[parent]["count"] += count

                        # Track child under parent
                        if child not in hierarchical_stats[parent]["children"]:
                            hierarchical_stats[parent]["children"][child] = {
                                "total": 0,
                                "avg": 0,
                                "max": 0,
                                "count": 0
                            }
                        hierarchical_stats[parent]["children"][child]["total"] += total
                        hierarchical_stats[parent]["children"][child]["count"] += count
                        hierarchical_stats[parent]["children"][child]["avg"] = (
                            hierarchical_stats[parent]["children"][child]["total"] /
                            hierarchical_stats[parent]["children"][child]["count"]
                        )
                        hierarchical_stats[parent]["children"][child]["max"] = max(
                            hierarchical_stats[parent]["children"][child]["max"],
                            max_dur
                        )
                    else:
                        # Non-hierarchical phase
                        flat_stats[phase] = {
                            "phase": phase,
                            "total": total,
                            "avg": avg,
                            "max": max_dur,
                            "count": count
                        }

                # Display hierarchical phases
                for parent, parent_data in sorted(
                    hierarchical_stats.items(),
                    key=lambda x: x[1]["total"],
                    reverse=True
                ):
                    parent_total = parent_data["total"]
                    parent_count = parent_data["count"]
                    parent_pct = (parent_total / total_duration * 100) if total_duration > 0 else 0

                    print(f"\n  📦 {parent}:")
                    print(
                        f"    Total: {int(parent_total):7d}ms ({parent_pct:5.1f}%) "
                        f"Count: {parent_count}"
                    )

                    # Show children
                    children_total = 0
                    for child, child_data in sorted(
                        parent_data["children"].items(),
                        key=lambda x: x[1]["total"],
                        reverse=True
                    ):
                        child_total = child_data["total"]
                        child_avg = child_data["avg"]
                        child_max = child_data["max"]
                        child_count = child_data["count"]
                        child_pct = (child_total / parent_total * 100) if parent_total > 0 else 0
                        children_total += child_total

                        print(
                            f"      ↳ {child:25s} {int(child_total):7d}ms ({child_pct:5.1f}%) "
                            f"Avg: {int(child_avg):6d}ms Max: {int(child_max):6d}ms Count: {child_count}"
                        )

                    # Calculate and show overhead
                    overhead = parent_total - children_total
                    if overhead > 0:
                        overhead_pct = (overhead / parent_total * 100) if parent_total > 0 else 0
                        print(
                            f"      ↳ {'[overhead]':25s} {int(overhead):7d}ms ({overhead_pct:5.1f}%)"
                        )

                # Display flat (non-hierarchical) phases
                if flat_stats:
                    print("\n  📋 Other Phases:")
                    for stat in sorted(
                        flat_stats.values(),
                        key=lambda x: x["total"],
                        reverse=True
                    )[:10]:
                        pct = (stat["total"] / total_duration * 100) if total_duration > 0 else 0
                        print(
                            f"    {stat['phase']:28s} Total: {int(stat['total']):7d}ms ({pct:5.1f}%) "
                            f"Avg: {int(stat['avg']):6d}ms Max: {int(stat['max']):6d}ms Count: {stat['count']}"
                        )

            print("\n⏱️  Per-Node Timing Breakdown:")
            for node_data in node_breakdown:
                node_id = node_data["node_id"]

                # Skip system node as it's shown separately
                if node_id == "system":
                    continue

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
                    print(f"    ├─ {phase:30s} {int(duration):7d}ms ({pct:5.1f}%)")

        if optimizations_only:
            optimizations = metrics.get("optimization_suggestions", [])
            if optimizations:
                print("\n💡 Optimization Suggestions:")
                for suggestion in optimizations:
                    print(f"  - {suggestion}")
            else:
                print("\n💡 No optimization suggestions available")
