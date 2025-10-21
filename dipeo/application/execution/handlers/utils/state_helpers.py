"""State query utilities for execution context."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dipeo.application.execution.engine.context import TypedExecutionContext
    from dipeo.diagram_generated.domain_models import NodeID
    from dipeo.diagram_generated.enums import Status


def get_node_execution_count(context: "TypedExecutionContext", node_id: "NodeID") -> int:
    """Get execution count for node."""
    return context.state.get_node_execution_count(node_id)


def get_node_status(context: "TypedExecutionContext", node_id: "NodeID") -> "Status | None":
    """Get current node status."""
    node_state = context.state.get_node_state(node_id)
    return node_state.status if node_state else None


def get_node_result(context: "TypedExecutionContext", node_id: "NodeID") -> Any | None:
    """Get node result output."""
    return context.state.get_node_result(node_id)


def has_node_executed(context: "TypedExecutionContext", node_id: "NodeID") -> bool:
    """Check if node has executed at least once."""
    return get_node_execution_count(context, node_id) > 0


def is_node_completed(context: "TypedExecutionContext", node_id: "NodeID") -> bool:
    """Check if node completed successfully."""
    from dipeo.diagram_generated.enums import Status

    status = get_node_status(context, node_id)
    return status == Status.COMPLETED


def get_all_node_results(
    context: "TypedExecutionContext", node_ids: list["NodeID"]
) -> dict["NodeID", Any]:
    """Collect results from multiple nodes."""
    results = {}
    for node_id in node_ids:
        result = get_node_result(context, node_id)
        if result is not None:
            results[node_id] = result
    return results
