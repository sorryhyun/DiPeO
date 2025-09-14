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

                icon = ICONS["success"] if status == "COMPLETED" else ICONS["error"]
                color = STATUS_COLORS.get(status, "white")

                duration_str = f"({duration:.1f}s)" if duration else ""
                node_text = Text(f"  {icon} {node_name}", style=color)
                node_text.append(f" {duration_str}", style="muted")
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


class ExecutionLayout:
    """Main layout manager for the execution display."""

    def __init__(self, diagram_name: str, execution_id: str):
        self.start_time = time.time()
        self.header = ExecutionHeader(diagram_name, execution_id, self.start_time)
        self.current_node = CurrentNodeDisplay()
        self.progress = NodeProgressDisplay()
        self.statistics = StatisticsDisplay()

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

    def render(self) -> RenderableType:
        """Render the complete layout."""
        # Create main layout
        layout = Layout()
        layout.split(
            Layout(self.header.render(), size=4, name="header"),
            Layout(name="body"),
            Layout(self.statistics.render(), size=8, name="stats"),
        )

        # Split body into current node and progress
        layout["body"].split_row(
            Layout(self.current_node.render(), name="current"),
            Layout(self.progress.render(), name="progress"),
        )

        return layout
