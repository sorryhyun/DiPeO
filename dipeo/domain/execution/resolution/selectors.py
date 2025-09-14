"""Edge selection and special input computation for domain-level resolution.

This module provides pure functions for selecting incoming edges and computing
special inputs for nodes during execution.
"""

from typing import Any

from dipeo.domain.diagram.models.executable_diagram import (
    ExecutableDiagram,
    ExecutableEdgeV2,
    ExecutableNode,
)
from dipeo.domain.execution.envelope import Envelope
from dipeo.domain.execution.execution_context import ExecutionContext

from .readiness import edge_is_ready, edge_matches_iteration_context, should_process_special_input


def incoming_edges(diagram: ExecutableDiagram, node: ExecutableNode) -> list[ExecutableEdgeV2]:
    """Find all edges targeting a node.

    Args:
        diagram: The executable diagram
        node: The target node

    Returns:
        List of edges targeting the node
    """
    return diagram.get_incoming_edges(node.id)


def select_incoming_edges(
    diagram: ExecutableDiagram, node: ExecutableNode, ctx: ExecutionContext
) -> list[ExecutableEdgeV2]:
    """Select edges that should contribute values to a node.

    This function filters edges based on:
    - Source node readiness
    - Iteration/branch context
    - Special input rules (e.g., PersonJob 'first' inputs)

    Args:
        diagram: The executable diagram
        node: The target node
        ctx: Execution context

    Returns:
        List of edges ready to be processed
    """
    edges = incoming_edges(diagram, node)

    has_special_inputs = has_node_special_inputs(node, edges)

    ready_edges = []
    for edge in edges:
        if not edge_is_ready(edge, node, ctx):
            continue

        if not should_process_special_input(edge, node, has_special_inputs):
            continue

        source_output = ctx.state.get_node_output(edge.source_node_id)
        if isinstance(source_output, Envelope):
            if not edge_matches_iteration_context(edge, ctx, source_output):
                continue

        ready_edges.append(edge)

    return ready_edges


def has_node_special_inputs(node: ExecutableNode, edges: list[ExecutableEdgeV2]) -> bool:
    """Check if a node has special inputs that affect edge processing.

    Args:
        node: The node to check
        edges: All edges targeting the node

    Returns:
        True if node has special inputs
    """
    from dipeo.diagram_generated import NodeType

    if node.type == NodeType.PERSON_JOB:
        return any(
            edge.target_input == "first" or edge.target_input.startswith("first.") for edge in edges
        )

    return False


def compute_special_inputs(node: ExecutableNode, ctx: ExecutionContext) -> dict[str, Any]:
    """Compute special inputs for a node that don't come from edges.

    This includes:
    - Default values for certain node types
    - Context-dependent inputs
    - Node-specific computed values
    - Loop indices exposed by condition nodes

    Args:
        node: The node to compute special inputs for
        ctx: Execution context

    Returns:
        Dictionary of special inputs (may be empty)
    """
    special_inputs: dict[str, Any] = {}

    from dipeo.diagram_generated import NodeType

    if hasattr(ctx, "get_variables"):
        variables = ctx.get_variables()
        for key, value in variables.items():
            if key not in special_inputs:
                special_inputs[key] = value

    if (
        node.type == NodeType.PERSON_JOB
        or node.type == NodeType.CONDITION
        or node.type == NodeType.API_JOB
    ):
        pass

    return special_inputs
