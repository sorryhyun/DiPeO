"""Edge selection and special input computation for domain-level resolution.

This module provides pure functions for selecting incoming edges and computing
special inputs for nodes during execution.
"""

from typing import Dict, Any

from dipeo.domain.diagram.models.executable_diagram import (
    ExecutableDiagram, 
    ExecutableNode, 
    ExecutableEdgeV2
)
from dipeo.domain.execution.execution_context import ExecutionContext
from dipeo.domain.execution.envelope import Envelope
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
    diagram: ExecutableDiagram, 
    node: ExecutableNode, 
    ctx: ExecutionContext
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
    
    # Check if node has special inputs (e.g., PersonJob 'first' inputs)
    has_special_inputs = has_node_special_inputs(node, edges)
    
    # Filter edges based on readiness and special input rules
    ready_edges = []
    for edge in edges:
        # Check basic readiness (source node completed)
        if not edge_is_ready(edge, node, ctx):
            continue
        
        # Check special input rules
        if not should_process_special_input(edge, node, has_special_inputs):
            continue
        
        # Check iteration/branch context if envelope available
        source_output = ctx.get_node_output(edge.source_node_id)
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
    
    # PersonJob nodes can have special 'first' inputs
    if node.type == NodeType.PERSON_JOB:
        return any(
            edge.target_input == "first" or edge.target_input.startswith("first.")
            for edge in edges
        )
    
    return False


def compute_special_inputs(node: ExecutableNode, ctx: ExecutionContext) -> Dict[str, Any]:
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
    special_inputs: Dict[str, Any] = {}
    
    from dipeo.diagram_generated import NodeType
    
    # Check for exposed loop indices from condition nodes
    # These are stored in variables (which persist across executions)
    # Add all variables to special inputs so they're available to nodes
    if hasattr(ctx, 'get_variables'):
        variables = ctx.get_variables()
        for key, value in variables.items():
            # Don't override explicit inputs with variables
            if key not in special_inputs:
                special_inputs[key] = value
    
    # PersonJob nodes may have default conversation context
    if node.type == NodeType.PERSON_JOB:
        # Check if we need to provide default conversation state
        # This would be based on node configuration and context state
        pass
    
    # Condition nodes may have default evaluation context
    elif node.type == NodeType.CONDITION:
        # Provide any default condition evaluation context
        pass
    
    # API nodes may have default headers or parameters
    elif node.type == NodeType.API_JOB:
        # Check for default API configuration
        pass
    
    return special_inputs