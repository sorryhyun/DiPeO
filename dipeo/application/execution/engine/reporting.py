"""Reporting utilities for execution state and progress.

This module provides functions for generating reports and summaries
from execution contexts without bloating the context itself.
"""

from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated import Status

if TYPE_CHECKING:
    from dipeo.application.execution.engine.context import TypedExecutionContext


def get_execution_summary(context: "TypedExecutionContext") -> dict[str, Any]:
    """Get execution summary from context's tracker."""
    return context.get_tracker().get_execution_summary()


def _count_by_status(context: "TypedExecutionContext", status_filter: list[Status]) -> int:
    """Count nodes matching any of the given statuses."""
    node_states = context.state.get_all_node_states()
    return sum(1 for state in node_states.values() if state.status in status_filter)


def count_nodes_by_status(context: "TypedExecutionContext", statuses: list[str]) -> int:
    """Count nodes by status names (e.g., ['COMPLETED', 'FAILED'])."""
    return _count_by_status(context, [Status[s] for s in statuses])


def calculate_progress(context: "TypedExecutionContext") -> dict[str, Any]:
    """Calculate execution progress with total_nodes, completed_nodes, and percentage."""
    node_states = context.state.get_all_node_states()
    total = len(node_states)
    completed = _count_by_status(context, [Status.COMPLETED, Status.MAXITER_REACHED])
    return {
        "total_nodes": total,
        "completed_nodes": completed,
        "percentage": (completed / total * 100) if total > 0 else 0,
    }


def get_completed_node_count(context: "TypedExecutionContext") -> int:
    """Get count of completed nodes (COMPLETED or MAXITER_REACHED)."""
    return _count_by_status(context, [Status.COMPLETED, Status.MAXITER_REACHED])


def get_failed_node_count(context: "TypedExecutionContext") -> int:
    """Get count of failed nodes."""
    return _count_by_status(context, [Status.FAILED])


def get_execution_metrics(context: "TypedExecutionContext") -> dict[str, Any]:
    """Get comprehensive execution metrics: progress, status_counts, tracker_summary, execution_id, diagram_id."""
    node_states = context.state.get_all_node_states()
    status_counts = {}
    for state in node_states.values():
        status_name = state.status.name
        status_counts[status_name] = status_counts.get(status_name, 0) + 1
    return {
        "progress": calculate_progress(context),
        "status_counts": status_counts,
        "tracker_summary": get_execution_summary(context),
        "execution_id": context.execution_id,
        "diagram_id": context.diagram_id,
    }
