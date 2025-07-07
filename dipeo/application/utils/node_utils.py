"""Node-related utility functions for the application layer."""

from typing import Any, Dict


def create_node_output(
    value: Dict[str, Any] | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Any:
    """Create a NodeOutput instance.
    
    Args:
        value: The output value dictionary
        metadata: Optional metadata dictionary
        
    Returns:
        NodeOutput instance
    """
    from dipeo.models import NodeOutput

    return NodeOutput(value=value or {}, metadata=metadata)