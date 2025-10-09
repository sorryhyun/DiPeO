"""State query utilities for execution context."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dipeo.application.execution.engine.context import TypedExecutionContext
    from dipeo.diagram_generated.domain_models import NodeID
    from dipeo.diagram_generated.enums import Status


def get_node_execution_count(context: "TypedExecutionContext", node_id: "NodeID") -> int:
    """Get execution count for a node.

    Args:
        context: Execution context
        node_id: Node identifier

    Returns:
        Number of times node has been executed

    Example:
        >>> count = get_node_execution_count(context, node.id)
        >>> if count >= 5:
        ...     print("Max iterations reached")
    """
    return context.state.get_node_execution_count(node_id)


def get_node_status(context: "TypedExecutionContext", node_id: "NodeID") -> "Status | None":
    """Get current status of a node.

    Args:
        context: Execution context
        node_id: Node identifier

    Returns:
        Node status or None if not found

    Example:
        >>> status = get_node_status(context, upstream_node.id)
        >>> if status == Status.COMPLETED:
        ...     print("Upstream node completed")
    """
    node_state = context.state.get_node_state(node_id)
    return node_state.status if node_state else None


def get_node_result(context: "TypedExecutionContext", node_id: "NodeID") -> Any | None:
    """Get result output from a node.

    Args:
        context: Execution context
        node_id: Node identifier

    Returns:
        Node result or None if not available

    Example:
        >>> result = get_node_result(context, dependency_node.id)
        >>> if result:
        ...     process_result(result)
    """
    return context.state.get_node_result(node_id)


def has_node_executed(context: "TypedExecutionContext", node_id: "NodeID") -> bool:
    """Check if a node has been executed at least once.

    Args:
        context: Execution context
        node_id: Node identifier

    Returns:
        True if node has executed, False otherwise

    Example:
        >>> if has_node_executed(context, init_node.id):
        ...     print("Initialization complete")
    """
    return get_node_execution_count(context, node_id) > 0


def is_node_completed(context: "TypedExecutionContext", node_id: "NodeID") -> bool:
    """Check if a node has completed successfully.

    Args:
        context: Execution context
        node_id: Node identifier

    Returns:
        True if node completed successfully, False otherwise

    Example:
        >>> if is_node_completed(context, prerequisite_node.id):
        ...     proceed_with_operation()
    """
    from dipeo.diagram_generated.enums import Status

    status = get_node_status(context, node_id)
    return status == Status.COMPLETED


def get_all_node_results(
    context: "TypedExecutionContext", node_ids: list["NodeID"]
) -> dict["NodeID", Any]:
    """Get results for multiple nodes.

    Args:
        context: Execution context
        node_ids: List of node identifiers

    Returns:
        Dictionary mapping node IDs to their results

    Example:
        >>> upstream_ids = [node1.id, node2.id, node3.id]
        >>> results = get_all_node_results(context, upstream_ids)
        >>> combined = combine_results(results.values())
    """
    results = {}
    for node_id in node_ids:
        result = get_node_result(context, node_id)
        if result is not None:
            results[node_id] = result
    return results
