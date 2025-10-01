"""UI components for the execution display."""

import time
from datetime import datetime
from typing import Any

from rich.align import Align
from rich.box import ROUNDED
from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from .styles import ICONS, NODE_TYPE_COLORS, SPINNER_FRAMES, STATUS_COLORS


class ExecutionHeader:
    """Header component showing diagram name, execution ID, and elapsed time."""

    def __init__(self, diagram_name: str, execution_id: str, start_time: float):
        self.diagram_name = diagram_name
        self.execution_id = execution_id
        self.start_time = start_time

    def render(self) -> RenderableType:
        elapsed = time.time() - self.start_time
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Create header content
        left = Text(f"{ICONS['diagram']} {self.diagram_name}", style="title")
        middle = Text(f"ID: {self.execution_id[:24]}...", style="muted")
        right = Text(f"{ICONS['time']} {time_str}", style="info")

        # Create table for alignment
        table = Table.grid(expand=True)
        table.add_column(justify="left", ratio=1)
        table.add_column(justify="center", ratio=1)
        table.add_column(justify="right", ratio=1)
        table.add_row(left, middle, right)

        return Panel(table, box=ROUNDED, title="DiPeO Execution", border_style="bright_blue")


class CurrentNodeDisplay:
    """Display component for the currently executing node."""

    def __init__(self):
        self.current_node = None
        self.node_start_time = None
        self.spinner_frame = 0

    def update(self, node_data: dict[str, Any] | None):
        """Update current node information."""
        if node_data:
            self.current_node = node_data
            if node_data.get("status") == "RUNNING" and not self.node_start_time:
                self.node_start_time = time.time()
        else:
            self.current_node = None
            self.node_start_time = None

    def render(self) -> RenderableType:
        if not self.current_node:
            content = Text("No node currently executing", style="muted")
            return Panel(content, box=ROUNDED, title="Current Node", border_style="dim")

        # Get node details
        node_id = self.current_node.get("node_id", "unknown")
        node_type = self.current_node.get("node_type", "UNKNOWN")
        status = self.current_node.get("status", "PENDING")
        node_name = self.current_node.get("name", node_id)

        # Create status indicator
        if status == "RUNNING":
            self.spinner_frame = (self.spinner_frame + 1) % len(SPINNER_FRAMES)
            status_icon = SPINNER_FRAMES[self.spinner_frame]
            status_text = f"{status_icon} {status}"
            elapsed = time.time() - self.node_start_time if self.node_start_time else 0
            elapsed_str = f" ({elapsed:.1f}s)"
        else:
            status_icon = ICONS.get(status.lower(), "")
            status_text = f"{status_icon} {status}"
            elapsed_str = ""

        # Create node display
        lines = [
            Text(f"{ICONS['running']} {node_name}", style="highlight"),
            Text(f"Type: {node_type}", style=NODE_TYPE_COLORS.get(node_type, "white")),
            Text(f"Status: {status_text}{elapsed_str}", style=STATUS_COLORS.get(status, "white")),
        ]

        # Add progress bar if running
        if status == "RUNNING" and self.node_start_time:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                expand=True,
            )
            task = progress.add_task("Processing...", total=None)
            lines.append(progress)

        return Panel(
            Group(*lines),
            box=ROUNDED,
            title="Current Node",
            border_style="yellow" if status == "RUNNING" else "dim",
        )


class NodeProgressDisplay:
    """Display component for overall node execution progress."""

    def __init__(self):
        self.total_nodes = 0
        self.completed_nodes = 0
        self.recent_nodes = []
        self.max_recent = 5

    def update(self, total: int, completed: int, recent_node: dict[str, Any] | None = None):
        """Update progress information."""
        self.total_nodes = total
        self.completed_nodes = completed
        if recent_node:
            self.recent_nodes.append(recent_node)
            if len(self.recent_nodes) > self.max_recent:
                self.recent_nodes.pop(0)

    def render(self) -> RenderableType:
        # Create progress bar
        if self.total_nodes > 0:
            percentage = (self.completed_nodes / self.total_nodes) * 100
            filled = int((self.completed_nodes / self.total_nodes) * 20)
            bar = "█" * filled + "░" * (20 - filled)
            progress_text = (
                f"Nodes: [{bar}] {self.completed_nodes}/{self.total_nodes} ({percentage:.0f}%)"
            )
        else:
            progress_text = "Nodes: Calculating..."

        lines = [Text(progress_text, style="info")]

        # Add recent nodes
        if self.recent_nodes:
            lines.append(Text())  # Empty line
            lines.append(Text("Recent:", style="subtitle"))

            for node in self.recent_nodes[-self.max_recent :]:
                node_name = node.get("name", node.get("node_id", "unknown"))
                node_type = node.get("node_type", "UNKNOWN")
                duration = node.get("duration", 0)
                status = node.get("status", "COMPLETED")
                person = node.get("person")
                tokens = node.get("tokens")

                icon = ICONS["success"] if status == "COMPLETED" else ICONS["error"]
                color = STATUS_COLORS.get(status, "white")

                # Build info string with duration, person, and tokens
                info_parts = []
                if duration:
                    info_parts.append(f"{duration:.1f}s")
                if person:
                    info_parts.append(f"{person}")
                if tokens:
                    info_parts.append(tokens)

                info_str = f" ({', '.join(info_parts)})" if info_parts else ""

                node_text = Text(f"  {icon} {node_name}", style=color)
                if info_str:
                    node_text.append(info_str, style="muted")
                lines.append(node_text)

        return Panel(Group(*lines), box=ROUNDED, title="Progress", border_style="info")


class StatisticsDisplay:
    """Display component for execution statistics."""

    def __init__(self):
        self.token_input = 0
        self.token_output = 0
        self.token_cached = 0
        self.errors = 0
        self.warnings = 0
        self.nodes_failed = 0
        self.nodes_skipped = 0

    def update(self, stats: dict[str, Any]):
        """Update statistics."""
        if "token_usage" in stats:
            tokens = stats["token_usage"]
            self.token_input = tokens.get("input", 0)
            self.token_output = tokens.get("output", 0)
            self.token_cached = tokens.get("cached", 0)

        self.errors = stats.get("errors", 0)
        self.warnings = stats.get("warnings", 0)
        self.nodes_failed = stats.get("nodes_failed", 0)
        self.nodes_skipped = stats.get("nodes_skipped", 0)

    def render(self) -> RenderableType:
        # Create statistics table
        table = Table(show_header=False, box=None, expand=True)
        table.add_column("label", style="muted")
        table.add_column("value", style="info")

        # Token usage
        total_tokens = self.token_input + self.token_output
        if total_tokens > 0:
            table.add_row(
                f"{ICONS['token']} Tokens:", f"{self.token_input:,} in / {self.token_output:,} out"
            )
            if self.token_cached > 0:
                table.add_row("", f"({self.token_cached:,} cached)")

        # Errors and warnings
        error_style = "error" if self.errors > 0 else "success"
        warning_style = "warning" if self.warnings > 0 else "muted"

        table.add_row("Errors:", Text(str(self.errors), style=error_style))
        table.add_row("Warnings:", Text(str(self.warnings), style=warning_style))

        # Node statistics
        if self.nodes_failed > 0 or self.nodes_skipped > 0:
            table.add_row("", "")  # Empty row for spacing
            if self.nodes_failed > 0:
                table.add_row("Failed nodes:", Text(str(self.nodes_failed), style="error"))
            if self.nodes_skipped > 0:
                table.add_row("Skipped nodes:", Text(str(self.nodes_skipped), style="muted"))

        return Panel(table, box=ROUNDED, title="Statistics", border_style="dim")


class LLMInteractionsDisplay:
    """Display component for LLM interactions including memory selection and token usage."""

    def __init__(self, debug: bool = False):
        self.recent_interactions = []
        self.max_recent = 5 if debug else 3
        self.debug = debug

    def add_interaction(
        self,
        node_id: str,
        person_id: str | None = None,
        model: str | None = None,
        token_usage: dict[str, Any] | None = None,
        memory_selection: dict[str, Any] | None = None,
        duration: float | None = None,
        debug: bool = False,
    ):
        """Add a new LLM interaction."""
        interaction = {
            "node_id": node_id,
            "person_id": person_id,
            "model": model,
            "token_usage": token_usage,
            "memory_selection": memory_selection,
            "duration": duration,
            "timestamp": time.time(),
        }
        self.recent_interactions.append(interaction)
        if len(self.recent_interactions) > self.max_recent:
            self.recent_interactions.pop(0)

    def render(self) -> RenderableType:
        if not self.recent_interactions:
            content = Text("No LLM interactions yet", style="muted")
            title = "LLM Interactions" + (" (Debug)" if self.debug else "")
            return Panel(content, box=ROUNDED, title=title, border_style="dim")

        lines = []
        for interaction in reversed(self.recent_interactions):  # Show most recent first
            node_id = interaction["node_id"]
            person_id = interaction.get("person_id", "unknown")
            model = interaction.get("model")

            # Node and person info
            lines.append(Text(f"{ICONS['running']} {node_id}", style="info"))
            # Show model prominently if available, otherwise show person_id
            if model:
                lines.append(Text(f"  Model: {model}", style="bright_cyan"))
                if person_id:
                    lines.append(Text(f"  Person: {person_id}", style="dim"))
            elif person_id:
                lines.append(Text(f"  Person: {person_id}", style="muted"))

            # Token usage
            if interaction.get("token_usage"):
                tokens = interaction["token_usage"]
                input_tokens = tokens.get("input", 0)
                output_tokens = tokens.get("output", 0)
                cached_tokens = tokens.get("cached", 0)

                token_text = f"  Tokens: {input_tokens:,} → {output_tokens:,}"
                if cached_tokens > 0:
                    token_text += f" (cached: {cached_tokens:,})"
                lines.append(Text(token_text, style="success"))

            # Memory selection info
            if interaction.get("memory_selection"):
                mem_sel = interaction["memory_selection"]
                total_messages = mem_sel.get("total_messages", 0)
                selected_count = mem_sel.get("selected_count", 0)
                selection_criteria = mem_sel.get("criteria", "")
                at_most = mem_sel.get("at_most", None)

                # Always show memory selection info when it exists
                if total_messages > 0:
                    mem_style = "success" if selected_count > 0 else "warning"
                    lines.append(
                        Text(
                            f"  Memory: {selected_count}/{total_messages} messages selected",
                            style=mem_style,
                        )
                    )
                    if selection_criteria:
                        lines.append(Text(f"    Criteria: {selection_criteria}", style="dim"))
                    if at_most:
                        lines.append(Text(f"    At most: {at_most} messages", style="dim"))
                elif total_messages == 0:
                    lines.append(
                        Text("  Memory: No messages available for selection", style="muted")
                    )

            # Duration
            if interaction.get("duration"):
                lines.append(Text(f"  Duration: {interaction['duration']:.2f}s", style="muted"))

            lines.append(Text())  # Empty line between interactions

        # Remove last empty line
        if lines and isinstance(lines[-1], Text) and not lines[-1].plain:
            lines.pop()

        # Add summary if in debug mode
        if self.debug and self.recent_interactions:
            total_selected = sum(
                i.get("memory_selection", {}).get("selected_count", 0)
                for i in self.recent_interactions
            )
            total_available = sum(
                i.get("memory_selection", {}).get("total_messages", 0)
                for i in self.recent_interactions
            )
            if total_available > 0:
                lines.insert(
                    0,
                    Text(
                        f"📊 Memory Selection: {total_selected}/{total_available} total messages used",
                        style="bright_cyan",
                    ),
                )
                lines.insert(1, Text())

        title = "LLM Interactions" + (" (Debug Mode)" if self.debug else "")
        return Panel(Group(*lines), box=ROUNDED, title=title, border_style="cyan")


class ExecutionLayout:
    """Main layout manager for the execution display."""

    def __init__(self, diagram_name: str, execution_id: str, debug: bool = False):
        self.start_time = time.time()
        self.debug = debug
        self.header = ExecutionHeader(diagram_name, execution_id, self.start_time)
        self.current_node = CurrentNodeDisplay()
        self.progress = NodeProgressDisplay()
        self.statistics = StatisticsDisplay()
        self.llm_interactions = LLMInteractionsDisplay(debug=debug)

    def update_node(self, node_data: dict[str, Any]):
        """Update node-related displays."""
        self.current_node.update(node_data)

    def update_progress(
        self, total: int, completed: int, recent_node: dict[str, Any] | None = None
    ):
        """Update progress display."""
        self.progress.update(total, completed, recent_node)

    def update_statistics(self, stats: dict[str, Any]):
        """Update statistics display."""
        self.statistics.update(stats)

    def update_llm_interaction(
        self,
        node_id: str,
        person_id: str | None = None,
        model: str | None = None,
        token_usage: dict[str, Any] | None = None,
        memory_selection: dict[str, Any] | None = None,
        duration: float | None = None,
        debug: bool = False,
    ):
        """Update LLM interactions display."""
        self.llm_interactions.add_interaction(
            node_id, person_id, model, token_usage, memory_selection, duration, debug=debug
        )

    def render(self) -> RenderableType:
        """Render the complete layout."""
        # Create main layout
        layout = Layout()
        layout.split(
            Layout(self.header.render(), size=4, name="header"),
            Layout(name="body"),
            Layout(name="bottom"),
        )

        # Split body into current node and progress
        layout["body"].split_row(
            Layout(self.current_node.render(), name="current"),
            Layout(self.progress.render(), name="progress"),
        )

        # Split bottom into statistics and LLM interactions
        layout["bottom"].split_row(
            Layout(self.statistics.render(), name="stats"),
            Layout(self.llm_interactions.render(), name="llm"),
        )

        return layout
