"""Main execution display controller using Rich Live display."""

import asyncio
import json
import threading
import time
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.live import Live

from .components import ExecutionLayout
from .styles import CLI_THEME


class ExecutionDisplay:
    """Controller for the rich execution display."""

    def __init__(self, diagram_name: str, execution_id: str, debug: bool = False):
        self.diagram_name = diagram_name
        self.execution_id = execution_id
        self.debug = debug

        # Create console with custom theme
        self.console = Console(theme=CLI_THEME)

        # Create layout
        self.layout = ExecutionLayout(diagram_name, execution_id)

        # State tracking
        self.nodes = {}
        self.node_order = []
        self.completed_count = 0
        self.total_count = 0
        self.current_node_id = None
        self.statistics = {
            "token_usage": {"input": 0, "output": 0, "cached": 0},
            "errors": 0,
            "warnings": 0,
            "nodes_failed": 0,
            "nodes_skipped": 0,
        }

        # Threading control
        self._stop_event = threading.Event()
        self._update_lock = threading.Lock()
        self._live = None
        self._update_thread = None

    def start(self):
        """Start the live display."""
        if self._live is None:
            # Clear the console and start fresh
            self.console.clear()

            # Render initial layout
            self._cached_layout = self.layout.render()
            self._live = Live(
                self._cached_layout,
                console=self.console,
                refresh_per_second=4,  # Balanced refresh rate
                screen=True,  # Use full screen mode for stable display
                vertical_overflow="ellipsis",  # Handle overflow properly
                transient=False,  # Keep display after completion
            )
            self._live.start()

            # Start update thread
            self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()

    def stop(self):
        """Stop the live display."""
        self._stop_event.set()
        if self._update_thread:
            self._update_thread.join(timeout=1)
        if self._live:
            self._live.stop()
            self._live = None

    def _update_loop(self):
        """Background thread to refresh the display."""
        while not self._stop_event.is_set():
            with self._update_lock:
                if self._live:
                    # Always update to keep the display fresh
                    self._live.update(self.layout.render())
            time.sleep(0.25)  # Update every 250ms to match 4fps refresh rate

    def handle_event(self, event: dict[str, Any]):
        """Handle an execution event and update the display."""
        event_type = event.get("event_type", event.get("type"))
        data = event.get("data", {})

        with self._update_lock:
            if event_type == "NODE_STARTED":
                self._handle_node_started(data)
            elif event_type == "NODE_COMPLETED":
                self._handle_node_completed(data)
            elif event_type == "NODE_FAILED":
                self._handle_node_failed(data)
            elif event_type == "NODE_STATUS_CHANGED":
                self._handle_node_status_changed(data)
            elif event_type == "EXECUTION_STATUS_CHANGED":
                self._handle_execution_status_changed(data)
            elif event_type == "METRICS_COLLECTED":
                self._handle_metrics(data)

    def _handle_node_started(self, data: dict[str, Any]):
        """Handle node started event."""
        node_id = data.get("node_id")
        if node_id:
            self.current_node_id = node_id

            # Store node info
            self.nodes[node_id] = {
                "node_id": node_id,
                "node_type": data.get("node_type", "UNKNOWN"),
                "name": data.get("name", node_id),
                "status": "RUNNING",
                "start_time": time.time(),
            }

            # Update displays
            self.layout.update_node(self.nodes[node_id])
            if node_id not in self.node_order:
                self.node_order.append(node_id)
                self.total_count = len(self.node_order)

            # Update progress
            self.layout.update_progress(self.total_count, self.completed_count)

    def _handle_node_completed(self, data: dict[str, Any]):
        """Handle node completed event."""
        node_id = data.get("node_id")
        if node_id and node_id in self.nodes:
            node = self.nodes[node_id]
            node["status"] = "COMPLETED"
            if "start_time" in node:
                node["duration"] = time.time() - node["start_time"]

            self.completed_count += 1

            # Clear current node if it was this one
            if self.current_node_id == node_id:
                self.current_node_id = None
                self.layout.update_node(None)

            # Update progress with recent node
            self.layout.update_progress(self.total_count, self.completed_count, node)

    def _handle_node_failed(self, data: dict[str, Any]):
        """Handle node failed event."""
        node_id = data.get("node_id")
        if node_id and node_id in self.nodes:
            node = self.nodes[node_id]
            node["status"] = "FAILED"
            node["error"] = data.get("error")
            if "start_time" in node:
                node["duration"] = time.time() - node["start_time"]

            self.statistics["nodes_failed"] += 1
            self.statistics["errors"] += 1

            # Clear current node if it was this one
            if self.current_node_id == node_id:
                self.current_node_id = None
                self.layout.update_node(None)

            # Update displays
            self.layout.update_progress(self.total_count, self.completed_count, node)
            self.layout.update_statistics(self.statistics)

    def _handle_node_status_changed(self, data: dict[str, Any]):
        """Handle node status change event."""
        node_id = data.get("node_id")
        status = data.get("status")

        if node_id and status:
            if node_id not in self.nodes:
                self.nodes[node_id] = {"node_id": node_id}

            self.nodes[node_id]["status"] = status

            if status == "SKIPPED":
                self.statistics["nodes_skipped"] += 1
                self.layout.update_statistics(self.statistics)

    def _handle_execution_status_changed(self, data: dict[str, Any]):
        """Handle execution status change event."""
        status = data.get("status")
        if status in ["COMPLETED", "FAILED", "ABORTED", "MAXITER_REACHED"]:
            # Clear current node display
            self.current_node_id = None
            self.layout.update_node(None)

    def _handle_metrics(self, data: dict[str, Any]):
        """Handle metrics update event."""
        if "token_usage" in data:
            self.statistics["token_usage"] = data["token_usage"]

        for key in ["errors", "warnings"]:
            if key in data:
                self.statistics[key] = data[key]

        self.layout.update_statistics(self.statistics)

    def update_from_state(self, execution_state: dict[str, Any]):
        """Update display from execution state (for initial state or recovery)."""
        with self._update_lock:
            # Update node states
            node_states = execution_state.get("node_states", {})
            for node_id, state in node_states.items():
                if node_id not in self.nodes:
                    self.nodes[node_id] = {
                        "node_id": node_id,
                        "node_type": state.get("node_type", "UNKNOWN"),
                        "name": state.get("name", node_id),
                        "status": state.get("status", "PENDING"),
                    }
                else:
                    self.nodes[node_id]["status"] = state.get("status", "PENDING")

                if state.get("status") == "COMPLETED":
                    self.completed_count += 1

            self.total_count = len(node_states)

            # Update token usage
            if "token_usage" in execution_state:
                self.statistics["token_usage"] = execution_state["token_usage"]

            # Update displays
            self.layout.update_progress(self.total_count, self.completed_count)
            self.layout.update_statistics(self.statistics)


@contextmanager
def execution_display(diagram_name: str, execution_id: str, debug: bool = False):
    """Context manager for execution display."""
    display = ExecutionDisplay(diagram_name, execution_id, debug)
    try:
        display.start()
        yield display
    finally:
        display.stop()


class SimpleDisplay:
    """Simple text-based display for compatibility mode."""

    def __init__(self, diagram_name: str, execution_id: str, debug: bool = False):
        self.diagram_name = diagram_name
        self.execution_id = execution_id
        self.debug = debug
        self.last_status = None

    def start(self):
        """Start simple display (no-op for simple mode)."""
        print(f"📄 Executing: {self.diagram_name}")
        print(f"🔑 ID: {self.execution_id}")

    def stop(self):
        """Stop simple display (no-op for simple mode)."""
        pass

    def handle_event(self, event: dict[str, Any]):
        """Handle event in simple mode."""
        event_type = event.get("event_type", event.get("type"))
        data = event.get("data", {})

        if event_type == "NODE_STARTED":
            node_id = data.get("node_id", "unknown")
            node_type = data.get("node_type", "")
            print(f"⚡ Starting node: {node_id} ({node_type})")
        elif event_type == "NODE_COMPLETED":
            node_id = data.get("node_id", "unknown")
            print(f"✓ Completed: {node_id}")
        elif event_type == "NODE_FAILED":
            node_id = data.get("node_id", "unknown")
            error = data.get("error", "Unknown error")
            print(f"✗ Failed: {node_id} - {error}")
        elif event_type == "EXECUTION_STATUS_CHANGED":
            status = data.get("status")
            if status != self.last_status:
                self.last_status = status
                print(f"📊 Execution status: {status}")

    def update_from_state(self, execution_state: dict[str, Any]):
        """Update from state in simple mode."""
        status = execution_state.get("status")
        if status and status != self.last_status:
            self.last_status = status
            print(f"📊 Status: {status}")
