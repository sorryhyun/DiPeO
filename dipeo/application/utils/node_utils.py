"""Node-related utility functions for the application layer."""

from typing import Any, Dict


def create_node_output(
    value: Dict[str, Any] | None = None,
    metadata: Dict[str, Any] | None = None,
    node_id: str | None = None,
    executed_nodes: list[str] | None = None,
) -> Any:
    """Create a NodeOutput instance.
    
    Args:
        value: The output value dictionary
        metadata: Optional metadata dictionary
        node_id: ID of the node that produced this output
        executed_nodes: List of node IDs executed up to this point
        
    Returns:
        NodeOutput instance
    """
    from dipeo.models import NodeOutput

    return NodeOutput(
        value=value or {}, 
        metadata=metadata,
        node_id=node_id,
        executed_nodes=executed_nodes
    )