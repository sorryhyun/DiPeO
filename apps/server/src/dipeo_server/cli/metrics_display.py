"""Metrics display formatting for CLI."""

from typing import Any


class MetricsDisplayManager:
    """Handles metrics display formatting."""

    PROMOTED_PHASES = {"llm_response", "memory_selection", "direct_execution"}

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

        MetricsDisplayManager._display_token_usage(metrics)

        if not optimizations_only:
            MetricsDisplayManager._display_bottlenecks(metrics, total_duration)

        if show_breakdown and node_breakdown:
            MetricsDisplayManager._display_system_operations(node_breakdown, total_duration)
            MetricsDisplayManager._display_node_phases(node_breakdown, total_duration)
            MetricsDisplayManager._display_per_node_breakdown(node_breakdown, total_duration)

        if optimizations_only:
            MetricsDisplayManager._display_optimizations(metrics)

    @staticmethod
    def _display_token_usage(metrics: dict[str, Any]) -> None:
        """Display token usage summary."""
        total_tokens = metrics.get("total_token_usage", {})
        if total_tokens and total_tokens.get("total", 0) > 0:
            print("\n🪙 Token Usage:")
            print(f"  Input:  {total_tokens.get('input', 0):,} tokens")
            print(f"  Output: {total_tokens.get('output', 0):,} tokens")
            print(f"  Total:  {total_tokens.get('total', 0):,} tokens")

    @staticmethod
    def _display_bottlenecks(metrics: dict[str, Any], total_duration: float) -> None:
        """Display top bottlenecks."""
        bottlenecks = metrics.get("bottlenecks", [])
        if bottlenecks:
            print("\n⚠️  Top Bottlenecks:")
            for i, bottleneck in enumerate(bottlenecks[:5], 1):
                if isinstance(bottleneck, dict):
                    node_id = bottleneck.get("node_id", "unknown")
                    node_type = bottleneck.get("node_type", "unknown")
                    duration = bottleneck.get("duration_ms", 0)
                    pct = (duration / total_duration * 100) if total_duration > 0 else 0
                    print(f"  {i}. {node_id} ({node_type}): {duration:.0f}ms ({pct:.1f}% of total)")
                else:
                    print(f"  {i}. {bottleneck}")

    @staticmethod
    def _display_system_operations(node_breakdown: list[dict], total_duration: float) -> None:
        """Display system-level operations timing."""
        system_phases = {}

        for node_data in node_breakdown:
            module_timings = node_data.get("module_timings", {})
            node_id = node_data.get("node_id", "")

            if node_id == "system":
                for phase, duration in module_timings.items():
                    if phase.endswith("__count") or phase.endswith("__max"):
                        if phase not in system_phases:
                            system_phases[phase] = []
                        system_phases[phase].append(duration)
                        continue

                    if phase not in system_phases:
                        system_phases[phase] = []
                    system_phases[phase].append(duration)

        if system_phases:
            print("\n🔧 System Operations Timing:")
            system_stats = []
            for phase, durations in system_phases.items():
                if phase.endswith("__count") or phase.endswith("__max"):
                    continue
                total = sum(durations)

                count_phase = f"{phase}__count"
                count = (
                    sum(system_phases[count_phase])
                    if count_phase in system_phases
                    else len(durations)
                )

                max_phase = f"{phase}__max"
                max_dur = (
                    max(system_phases[max_phase])
                    if max_phase in system_phases
                    else max(durations)
                    if durations
                    else 0
                )

                avg = total / count if count > 0 else 0
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

    @staticmethod
    def _display_node_phases(node_breakdown: list[dict], total_duration: float) -> None:
        """Display node-level phases with hierarchical structure."""
        node_phases = {}

        for node_data in node_breakdown:
            module_timings = node_data.get("module_timings", {})
            node_id = node_data.get("node_id", "")

            if node_id != "system":
                for phase, duration in module_timings.items():
                    if phase.endswith("__count") or phase.endswith("__max"):
                        if phase not in node_phases:
                            node_phases[phase] = []
                        node_phases[phase].append(duration)
                        continue

                    if phase not in node_phases:
                        node_phases[phase] = []
                    node_phases[phase].append(duration)

        if not node_phases:
            return

        print("\n⏱️  Node Phase Timing Summary:")

        hierarchical_stats = {}
        flat_stats = {}

        for phase, durations in node_phases.items():
            if phase.endswith("__count") or phase.endswith("__max"):
                continue

            total = sum(durations)

            count_phase = f"{phase}__count"
            count = sum(node_phases[count_phase]) if count_phase in node_phases else len(durations)

            max_phase = f"{phase}__max"
            max_dur = (
                max(node_phases[max_phase])
                if max_phase in node_phases
                else max(durations)
                if durations
                else 0
            )

            avg = total / count if count > 0 else 0

            if "__" in phase:
                belongs_to_promoted = None
                for promoted in MetricsDisplayManager.PROMOTED_PHASES:
                    if phase.startswith(f"{promoted}__"):
                        belongs_to_promoted = promoted
                        break

                if belongs_to_promoted:
                    if belongs_to_promoted not in hierarchical_stats:
                        hierarchical_stats[belongs_to_promoted] = {
                            "total": 0,
                            "count": 0,
                            "children": {},
                            "is_promoted": True,
                            "avg": 0,
                            "max": 0,
                        }

                    sub_phase = phase.replace(f"{belongs_to_promoted}__", "", 1)

                    if sub_phase not in hierarchical_stats[belongs_to_promoted]["children"]:
                        hierarchical_stats[belongs_to_promoted]["children"][sub_phase] = {
                            "total": 0,
                            "avg": 0,
                            "max": 0,
                            "count": 0,
                        }
                    hierarchical_stats[belongs_to_promoted]["children"][sub_phase]["total"] += total
                    hierarchical_stats[belongs_to_promoted]["children"][sub_phase]["count"] += count
                    hierarchical_stats[belongs_to_promoted]["children"][sub_phase]["max"] = max(
                        hierarchical_stats[belongs_to_promoted]["children"][sub_phase]["max"],
                        max_dur,
                    )
                    hierarchical_stats[belongs_to_promoted]["children"][sub_phase]["avg"] = (
                        hierarchical_stats[belongs_to_promoted]["children"][sub_phase]["total"]
                        / hierarchical_stats[belongs_to_promoted]["children"][sub_phase]["count"]
                    )

                    hierarchical_stats[belongs_to_promoted]["total"] += total
                    hierarchical_stats[belongs_to_promoted]["count"] += count
                    hierarchical_stats[belongs_to_promoted]["avg"] = (
                        hierarchical_stats[belongs_to_promoted]["total"]
                        / hierarchical_stats[belongs_to_promoted]["count"]
                        if hierarchical_stats[belongs_to_promoted]["count"] > 0
                        else 0
                    )
                    hierarchical_stats[belongs_to_promoted]["max"] = max(
                        hierarchical_stats[belongs_to_promoted]["max"], max_dur
                    )
                else:
                    parent, child = phase.split("__", 1)

                    if parent not in hierarchical_stats:
                        hierarchical_stats[parent] = {"total": 0, "count": 0, "children": {}}
                    hierarchical_stats[parent]["total"] += total
                    hierarchical_stats[parent]["count"] += count

                    if child not in hierarchical_stats[parent]["children"]:
                        hierarchical_stats[parent]["children"][child] = {
                            "total": 0,
                            "avg": 0,
                            "max": 0,
                            "count": 0,
                        }
                    hierarchical_stats[parent]["children"][child]["total"] += total
                    hierarchical_stats[parent]["children"][child]["count"] += count
                    hierarchical_stats[parent]["children"][child]["max"] = max(
                        hierarchical_stats[parent]["children"][child]["max"], max_dur
                    )
                    hierarchical_stats[parent]["children"][child]["avg"] = (
                        hierarchical_stats[parent]["children"][child]["total"]
                        / hierarchical_stats[parent]["children"][child]["count"]
                    )
            elif phase in MetricsDisplayManager.PROMOTED_PHASES:
                if phase not in hierarchical_stats:
                    hierarchical_stats[phase] = {
                        "total": 0,
                        "count": 0,
                        "children": {},
                        "is_promoted": True,
                        "avg": 0,
                        "max": 0,
                    }
                hierarchical_stats[phase]["total"] += total
                hierarchical_stats[phase]["count"] += count
                # Calculate avg from accumulated total/count, don't just overwrite
                hierarchical_stats[phase]["avg"] = (
                    hierarchical_stats[phase]["total"] / hierarchical_stats[phase]["count"]
                    if hierarchical_stats[phase]["count"] > 0
                    else 0
                )
                # Take maximum across all max_dur values
                hierarchical_stats[phase]["max"] = max(hierarchical_stats[phase]["max"], max_dur)
            else:
                flat_stats[phase] = {
                    "phase": phase,
                    "total": total,
                    "avg": avg,
                    "max": max_dur,
                    "count": count,
                }

        MetricsDisplayManager._display_hierarchical_phases(hierarchical_stats, total_duration)
        MetricsDisplayManager._display_flat_phases(flat_stats, total_duration)

    @staticmethod
    def _display_hierarchical_phases(hierarchical_stats: dict, total_duration: float) -> None:
        """Display hierarchical phases."""
        for parent, parent_data in sorted(
            hierarchical_stats.items(), key=lambda x: x[1]["total"], reverse=True
        ):
            parent_total = parent_data["total"]
            parent_count = parent_data.get("count", 0)
            parent_pct = (parent_total / total_duration * 100) if total_duration > 0 else 0

            is_promoted = parent_data.get("is_promoted", False)
            has_children = len(parent_data["children"]) > 0

            if is_promoted:
                parent_avg = parent_data.get("avg", 0)
                parent_max = parent_data.get("max", 0)

                print(f"\n  📦 {parent}:")
                if parent_avg > 0 or parent_max > 0:
                    print(
                        f"    Total: {int(parent_total):7d}ms ({parent_pct:5.1f}%) "
                        f"Avg: {int(parent_avg):6d}ms Max: {int(parent_max):6d}ms Count: {parent_count}"
                    )
                else:
                    print(f"    Total: {int(parent_total):7d}ms ({parent_pct:5.1f}%)")

                if has_children:
                    children_total = 0
                    for child, child_data in sorted(
                        parent_data["children"].items(), key=lambda x: x[1]["total"], reverse=True
                    ):
                        if child.endswith("_count") or child.endswith("_max"):
                            continue
                        child_total = child_data["total"]
                        child_avg = child_data["avg"]
                        child_max = child_data["max"]
                        child_count = child_data["count"]
                        child_pct = (child_total / parent_total * 100) if parent_total > 0 else 0
                        children_total += child_total

                        print(
                            f"      ↳ {child:30s} {int(child_total):7d}ms ({child_pct:5.1f}%) "
                            f"Avg: {int(child_avg):6d}ms Max: {int(child_max):6d}ms Count: {child_count}"
                        )

                    overhead = parent_total - children_total
                    if overhead > 0:
                        overhead_pct = (overhead / parent_total * 100) if parent_total > 0 else 0
                        print(
                            f"      ↳ {'[overhead/core]':30s} {int(overhead):7d}ms ({overhead_pct:5.1f}%)"
                        )
            elif has_children:
                print(f"\n  📦 {parent}:")
                print(
                    f"    Total: {int(parent_total):7d}ms ({parent_pct:5.1f}%) "
                    f"Count: {parent_count}"
                )

                children_total = 0
                for child, child_data in sorted(
                    parent_data["children"].items(), key=lambda x: x[1]["total"], reverse=True
                ):
                    if child.endswith("_count") or child.endswith("_max"):
                        continue
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

                overhead = parent_total - children_total
                if overhead > 0:
                    overhead_pct = (overhead / parent_total * 100) if parent_total > 0 else 0
                    print(f"      ↳ {'[overhead]':25s} {int(overhead):7d}ms ({overhead_pct:5.1f}%)")

    @staticmethod
    def _display_flat_phases(flat_stats: dict, total_duration: float) -> None:
        """Display flat (non-hierarchical) phases."""
        if flat_stats:
            print("\n  📋 Other Phases:")
            for stat in sorted(flat_stats.values(), key=lambda x: x["total"], reverse=True)[:10]:
                pct = (stat["total"] / total_duration * 100) if total_duration > 0 else 0
                print(
                    f"    {stat['phase']:28s} Total: {int(stat['total']):7d}ms ({pct:5.1f}%) "
                    f"Avg: {int(stat['avg']):6d}ms Max: {int(stat['max']):6d}ms Count: {stat['count']}"
                )

    @staticmethod
    def _display_per_node_breakdown(node_breakdown: list[dict], total_duration: float) -> None:
        """Display per-node timing breakdown."""
        print("\n⏱️  Per-Node Timing Breakdown:")

        nodes_by_base_id = {}
        for node_data in node_breakdown:
            metrics_key = node_data["node_id"]

            if metrics_key == "system":
                continue

            if "_iter_" in metrics_key:
                parts = metrics_key.rsplit("_iter_", 1)
                base_node_id = parts[0]
                iteration = int(parts[1])
            else:
                base_node_id = metrics_key
                iteration = None

            if base_node_id not in nodes_by_base_id:
                nodes_by_base_id[base_node_id] = []
            nodes_by_base_id[base_node_id].append((iteration, node_data, metrics_key))

        for base_node_id in sorted(nodes_by_base_id.keys()):
            iterations = sorted(
                nodes_by_base_id[base_node_id], key=lambda x: x[0] if x[0] is not None else 0
            )

            has_real_iterations = any(it[0] is not None for it in iterations)
            if has_real_iterations:
                iterations = [it for it in iterations if it[0] is not None]

            if not iterations:
                continue

            if len(iterations) == 1 and iterations[0][0] is None:
                MetricsDisplayManager._display_single_node(
                    iterations[0], base_node_id, total_duration
                )
            else:
                MetricsDisplayManager._display_iterated_node(
                    iterations, base_node_id, total_duration
                )

    @staticmethod
    def _display_single_node(
        iteration_data: tuple, base_node_id: str, total_duration: float
    ) -> None:
        """Display single node timing."""
        iteration, node_data, metrics_key = iteration_data
        node_type = node_data.get("node_type", "unknown")
        total_ms = node_data.get("duration_ms", 0)
        module_timings = node_data.get("module_timings", {})
        token_usage = node_data.get("token_usage", {})

        if not module_timings:
            return

        pct_of_total = (total_ms / total_duration * 100) if total_duration > 0 else 0
        token_str = ""
        if token_usage and token_usage.get("total", 0) > 0:
            token_str = f" | Tokens: {token_usage.get('total', 0):,}"

        print(
            f"\n  {base_node_id} ({node_type}) - {total_ms:.0f}ms ({pct_of_total:.1f}%){token_str}"
        )

        sorted_phases = sorted(
            [
                (p, d)
                for p, d in module_timings.items()
                if not p.endswith("__count") and not p.endswith("__max")
            ],
            key=lambda x: x[1],
            reverse=True,
        )

        for phase, duration in sorted_phases:
            pct = (duration / total_ms * 100) if total_ms > 0 else 0
            print(f"    ├─ {phase:30s} {int(duration):7d}ms ({pct:5.1f}%)")

    @staticmethod
    def _display_iterated_node(iterations: list, base_node_id: str, total_duration: float) -> None:
        """Display iterated node timing."""
        total_iterations = len(iterations)
        total_time = sum(node_data.get("duration_ms", 0) for _, node_data, _ in iterations)
        node_type = iterations[0][1].get("node_type", "unknown")
        pct_of_total = (total_time / total_duration * 100) if total_duration > 0 else 0

        print(
            f"\n  {base_node_id} ({node_type}) - {total_iterations} iterations, {total_time:.0f}ms total ({pct_of_total:.1f}%)"
        )

        for iteration, node_data, _metrics_key in iterations:
            total_ms = node_data.get("duration_ms", 0)
            token_usage = node_data.get("token_usage", {})
            module_timings = node_data.get("module_timings", {})

            token_str = ""
            if token_usage and token_usage.get("total", 0) > 0:
                token_str = f" | Tokens: {token_usage.get('total', 0):,}"

            print(f"    └─ Iteration {iteration}: {total_ms:.0f}ms{token_str}")

            if module_timings:
                sorted_phases = sorted(
                    [
                        (p, d)
                        for p, d in module_timings.items()
                        if not p.endswith("__count") and not p.endswith("__max")
                    ],
                    key=lambda x: x[1],
                    reverse=True,
                )
                for phase, duration in sorted_phases[:3]:
                    pct = (duration / total_ms * 100) if total_ms > 0 else 0
                    print(f"       ├─ {phase:30s} {int(duration):7d}ms ({pct:5.1f}%)")

    @staticmethod
    def _display_optimizations(metrics: dict[str, Any]) -> None:
        """Display optimization suggestions."""
        optimizations = metrics.get("optimization_suggestions", [])
        if optimizations:
            print("\n💡 Optimization Suggestions:")
            for suggestion in optimizations:
                print(f"  - {suggestion}")
        else:
            print("\n💡 No optimization suggestions available")
