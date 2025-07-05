"""
Handle ID utilities for managing handle IDs.
This is a manually maintained file, not auto-generated.
"""

from typing import Tuple
from dipeo_domain import HandleID, NodeID, HandleDirection


def create_handle_id(
    node_id: NodeID,
    handle_label: str,
    direction: HandleDirection
) -> HandleID:
    """Create a handle ID from node ID, handle label, and direction.
    Format: [nodeId]_[handleLabel]_[direction]
    """
    # Use underscores for simpler format
    return HandleID(f"{node_id}_{handle_label}_{direction.value}")


def parse_handle_id(
    handle_id: HandleID
) -> Tuple[NodeID, str, HandleDirection]:
    """Parse a handle ID into its components.
    Returns (node_id, handle_label, direction)
    """
    # Format: [nodeId]_[handleLabel]_[direction]
    parts = handle_id.split('_')
    if len(parts) < 3:
        raise ValueError(f"Invalid handle ID format: {handle_id}")
    
    # Extract parts: nodeId_label_direction
    direction_str = parts[-1]
    handle_label = parts[-2]
    node_id_parts = parts[:-2]
    node_id = '_'.join(node_id_parts)
    
    # Validate direction
    try:
        direction = HandleDirection(direction_str)
    except ValueError:
        raise ValueError(f"Invalid direction in handle ID: {handle_id}")
    
    if not node_id or not handle_label:
        raise ValueError(f"Invalid handle ID format: {handle_id}")
    
    return NodeID(node_id), handle_label, direction