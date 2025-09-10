"""Edge readiness checks for domain-level input resolution.

This module contains pure functions to determine if edges should contribute
their values during execution, based on dependency states, branching, and iteration.
"""

from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2, ExecutableNode
from dipeo.domain.execution.envelope import Envelope
from dipeo.domain.execution.execution_context import ExecutionContext


def edge_is_ready(edge: ExecutableEdgeV2, node: ExecutableNode, ctx: ExecutionContext) -> bool:
    """Determine if an edge should contribute its value in the current execution state.

    This pure function checks:
    - Source node completion status
    - Iteration context matching
    - Branch context matching

    Args:
        edge: The edge to check
        node: The target node receiving the input
        ctx: Execution context for state queries

    Returns:
        True if the edge should be processed, False otherwise
    """
    src_id = edge.source_node_id
    src_state = ctx.state.get_node_state(src_id)

    if not src_state:
        return False

    from dipeo.diagram_generated import Status

    is_completed = hasattr(src_state, "status") and src_state.status == Status.COMPLETED

    if not is_completed:
        return False

    return not (hasattr(src_state, "status") and src_state.status == Status.FAILED)


def edge_matches_iteration_context(
    edge: ExecutableEdgeV2, ctx: ExecutionContext, envelope: Envelope | None = None
) -> bool:
    """Check if edge matches the current iteration context.

    Args:
        edge: The edge to check
        ctx: Execution context
        envelope: Optional envelope with metadata to check

    Returns:
        True if edge matches iteration context, False otherwise
    """
    if not envelope or not isinstance(envelope, Envelope):
        return True

    if "iteration" in envelope.meta:
        target_state = ctx.state.get_node_state(edge.target_node_id)
        if target_state and hasattr(target_state, "iteration_count"):
            current_iteration = target_state.iteration_count
            if envelope.meta["iteration"] != current_iteration:
                return False

    if "branch_id" in envelope.meta:
        target_state = ctx.state.get_node_state(edge.target_node_id)
        if target_state and hasattr(target_state, "active_branch"):
            active_branch = target_state.active_branch
            if envelope.meta["branch_id"] != active_branch:
                return False

    return True


def should_process_special_input(
    edge: ExecutableEdgeV2, node: ExecutableNode, has_special_inputs: bool
) -> bool:
    """Determine if an edge should be processed based on special input rules.

    For PersonJob nodes with 'first' inputs, only those inputs are processed
    when special inputs are present.

    Args:
        edge: The edge to check
        node: The target node
        has_special_inputs: Whether the node has special inputs

    Returns:
        True if edge should be processed, False otherwise
    """
    from dipeo.diagram_generated import NodeType

    if not has_special_inputs:
        return True

    if node.type == NodeType.PERSON_JOB:
        return edge.target_input == "first" or edge.target_input.startswith("first.")

    return True
