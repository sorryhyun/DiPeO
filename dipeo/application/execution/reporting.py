"""Reporting utilities for execution state and progress.

This module provides functions for generating reports and summaries
from execution contexts without bloating the context itself.
"""

from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated import Status

if TYPE_CHECKING:
    from dipeo.application.execution.typed_execution_context import TypedExecutionContext


def get_execution_summary(context: "TypedExecutionContext") -> dict[str, Any]:
    """Get execution summary from context's tracker."""
    return context.get_tracker().get_execution_summary()


def count_nodes_by_status(context: "TypedExecutionContext", statuses: list[str]) -> int:
    """Count nodes by status in the context."""
    status_enums = [Status[status] for status in statuses]
    node_states = context.state.get_all_node_states()
    return sum(1 for state in node_states.values() if state.status in status_enums)


def calculate_progress(context: "TypedExecutionContext") -> dict[str, Any]:
    """Calculate execution progress from context state."""
    node_states = context.state.get_all_node_states()
    total = len(node_states)
    completed = sum(
        1
        for state in node_states.values()
        if state.status in [Status.COMPLETED, Status.MAXITER_REACHED]
    )

    return {
        "total_nodes": total,
        "completed_nodes": completed,
        "percentage": (completed / total * 100) if total > 0 else 0,
    }


def get_completed_node_count(context: "TypedExecutionContext") -> int:
    """Get count of completed nodes."""
    node_states = context.state.get_all_node_states()
    return sum(
        1
        for state in node_states.values()
        if state.status in [Status.COMPLETED, Status.MAXITER_REACHED]
    )


def get_failed_node_count(context: "TypedExecutionContext") -> int:
    """Get count of failed nodes."""
    node_states = context.state.get_all_node_states()
    return sum(1 for state in node_states.values() if state.status == Status.FAILED)


def get_execution_metrics(context: "TypedExecutionContext") -> dict[str, Any]:
    """Get comprehensive execution metrics."""
    node_states = context.state.get_all_node_states()

    # Count by status
    status_counts = {}
    for state in node_states.values():
        status_name = state.status.name
        status_counts[status_name] = status_counts.get(status_name, 0) + 1

    # Calculate progress
    progress = calculate_progress(context)

    # Get tracker summary
    tracker_summary = context.get_tracker().get_execution_summary()

    return {
        "progress": progress,
        "status_counts": status_counts,
        "tracker_summary": tracker_summary,
        "execution_id": context.execution_id,
        "diagram_id": context.diagram_id,
    }
