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
        self.layout = ExecutionLayout(diagram_name, execution_id, debug=debug)

        # Display-only state (minimal tracking for UI rendering)
        # We only track what's needed for the current display, not the full execution state
        self.current_node_display = None  # Current node being displayed
        self.completed_count = 0
        self.total_count = 0
        self.last_completed_node = None  # For showing recent progress

        # Statistics for display only (updated from events)
        self.display_stats = {
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
            elif event_type in ["EXECUTION_STARTED", "execution_started"]:
                self._handle_execution_started(data)
            elif event_type in ["EXECUTION_COMPLETED", "execution_completed"]:
                self._handle_execution_completed(data)
            elif event_type in ["EXECUTION_ERROR", "execution_error"]:
                self._handle_execution_error(data)
            elif event_type == "METRICS_COLLECTED":
                self._handle_metrics(data)

    def _handle_node_started(self, data: dict[str, Any]):
        """Handle node started event."""
        node_id = data.get("node_id")
        if node_id:
            # Create display info for current node
            self.current_node_display = {
                "node_id": node_id,
                "node_type": data.get("node_type", "UNKNOWN"),
                "name": data.get("name", node_id),
                "status": "RUNNING",
                "start_time": time.time(),
            }

            # Update displays
            self.layout.update_node(self.current_node_display)

            # Increment total count if this is a new node
            # (we can detect this from the event data if needed)
            if data.get("is_new_node", True):
                self.total_count += 1

            # Update progress
            self.layout.update_progress(self.total_count, self.completed_count)

    def _handle_node_completed(self, data: dict[str, Any]):
        """Handle node completed event."""
        node_id = data.get("node_id")
        if node_id:
            self.completed_count += 1

            # Create a display record for the completed node
            completed_node = {
                "node_id": node_id,
                "node_type": data.get("node_type", "UNKNOWN"),
                "name": data.get("name", node_id),
                "status": "COMPLETED",
            }

            # Add person info if this was a person_job node
            person_id = data.get("person_id")
            if person_id:
                completed_node["person"] = person_id

            # Add duration if we were tracking this node
            duration = None
            if (
                self.current_node_display
                and self.current_node_display.get("node_id") == node_id
                and "start_time" in self.current_node_display
            ):
                duration = time.time() - self.current_node_display["start_time"]
                completed_node["duration"] = duration

            # Extract memory selection info
            memory_selection = data.get("memory_selection")

            # Accumulate token usage if present
            token_usage = data.get("token_usage")
            if token_usage and isinstance(token_usage, dict):
                input_tokens = token_usage.get("input", 0)
                output_tokens = token_usage.get("output", 0)

                self.display_stats["token_usage"]["input"] += input_tokens
                self.display_stats["token_usage"]["output"] += output_tokens
                # Calculate total from input + output if not provided
                total = token_usage.get("total", 0)
                if total == 0 and (input_tokens or output_tokens):
                    total = input_tokens + output_tokens
                self.display_stats["token_usage"]["total"] = (
                    self.display_stats["token_usage"]["input"]
                    + self.display_stats["token_usage"]["output"]
                )
                # Update statistics display with new token counts
                self.layout.update_statistics(self.display_stats)
                # Add token info to completed node for display
                completed_node["tokens"] = f"in:{input_tokens} out:{output_tokens}"

            # Update LLM interactions panel if this was an LLM node
            if person_id or token_usage:
                self.layout.update_llm_interaction(
                    node_id=node_id,
                    person_id=person_id,
                    token_usage=token_usage,
                    memory_selection=memory_selection,
                    duration=duration,
                    debug=self.debug,
                )

            self.last_completed_node = completed_node

            # Clear current node if it was this one
            if self.current_node_display and self.current_node_display.get("node_id") == node_id:
                self.current_node_display = None
                self.layout.update_node(None)

            # Update progress with recent node
            self.layout.update_progress(self.total_count, self.completed_count, completed_node)

    def _handle_node_failed(self, data: dict[str, Any]):
        """Handle node failed event."""
        node_id = data.get("node_id")
        if node_id:
            # Create a display record for the failed node
            failed_node = {
                "node_id": node_id,
                "node_type": data.get("node_type", "UNKNOWN"),
                "name": data.get("name", node_id),
                "status": "FAILED",
                "error": data.get("error"),
            }

            # Add duration if we were tracking this node
            if (
                self.current_node_display
                and self.current_node_display.get("node_id") == node_id
                and "start_time" in self.current_node_display
            ):
                failed_node["duration"] = time.time() - self.current_node_display["start_time"]

            self.display_stats["nodes_failed"] += 1
            self.display_stats["errors"] += 1

            # Clear current node if it was this one
            if self.current_node_display and self.current_node_display.get("node_id") == node_id:
                self.current_node_display = None
                self.layout.update_node(None)

            # Update displays
            self.layout.update_progress(self.total_count, self.completed_count, failed_node)
            self.layout.update_statistics(self.display_stats)

    def _handle_node_status_changed(self, data: dict[str, Any]):
        """Handle node status change event."""
        status = data.get("status")

        if status == "SKIPPED":
            self.display_stats["nodes_skipped"] += 1
            self.layout.update_statistics(self.display_stats)

    def _handle_execution_started(self, data: dict[str, Any]):
        """Handle execution started event."""
        # Execution has started, no specific action needed for display
        pass

    def _handle_execution_completed(self, data: dict[str, Any]):
        """Handle execution completed event."""
        # Clear current node display
        self.current_node_display = None
        self.layout.update_node(None)

    def _handle_execution_error(self, data: dict[str, Any]):
        """Handle execution error event."""
        # Clear current node display
        self.current_node_display = None
        self.layout.update_node(None)

    def _handle_metrics(self, data: dict[str, Any]):
        """Handle metrics update event."""
        if "token_usage" in data:
            self.display_stats["token_usage"] = data["token_usage"]

        for key in ["errors", "warnings"]:
            if key in data:
                self.display_stats[key] = data[key]

        self.layout.update_statistics(self.display_stats)

    def update_from_state(self, execution_state: dict[str, Any]):
        """Update display from execution state (for initial state or recovery)."""
        with self._update_lock:
            # Only extract display-relevant information from the state
            node_states = execution_state.get("node_states", {})

            # Count completed nodes
            self.completed_count = sum(
                1 for state in node_states.values() if state.get("status") == "COMPLETED"
            )
            self.total_count = len(node_states)

            # Update token usage
            if "token_usage" in execution_state:
                self.display_stats["token_usage"] = execution_state["token_usage"]

            # Update displays
            self.layout.update_progress(self.total_count, self.completed_count)
            self.layout.update_statistics(self.display_stats)


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
        elif event_type in ["EXECUTION_STARTED", "execution_started"]:
            print("📊 Execution started")
        elif event_type in ["EXECUTION_COMPLETED", "execution_completed"]:
            print("📊 Execution completed")
        elif event_type in ["EXECUTION_ERROR", "execution_error"]:
            error = data.get("error", "Unknown error")
            print(f"📊 Execution failed: {error}")

    def update_from_state(self, execution_state: dict[str, Any]):
        """Update from state in simple mode."""
        status = execution_state.get("status")
        if status and status != self.last_status:
            self.last_status = status
            print(f"📊 Status: {status}")
