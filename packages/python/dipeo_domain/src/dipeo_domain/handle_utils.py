"""
Handle ID utilities for managing handle IDs.
This is a manually maintained file, not auto-generated.
"""

from typing import Tuple
from dipeo_domain import HandleID, NodeID, HandleDirection, HandleLabel


def create_handle_id(
    node_id: NodeID,
    handle_label: HandleLabel,
    direction: HandleDirection
) -> HandleID:
    """Create a handle ID from node ID, handle label, and direction.
    Format: [nodeId]_[handleLabel]_[direction]
    """
    # Use underscores for simpler format
    return HandleID(f"{node_id}_{handle_label.value}_{direction.value}")


def parse_handle_id(
    handle_id: HandleID
) -> Tuple[NodeID, HandleLabel, HandleDirection]:
    """Parse a handle ID into its components.
    Returns (node_id, handle_label, direction)
    """
    # Format: [nodeId]_[handleLabel]_[direction]
    parts = handle_id.split('_')
    if len(parts) < 3:
        raise ValueError(f"Invalid handle ID format: {handle_id}")
    
    # Extract parts: nodeId_label_direction
    direction_str = parts[-1]
    handle_label_str = parts[-2]
    node_id_parts = parts[:-2]
    node_id = '_'.join(node_id_parts)
    
    if not node_id:
        raise ValueError(f"Invalid handle ID format: {handle_id}")
    
    # Since handle IDs are created by our system, we can trust the enum values
    direction = HandleDirection(direction_str)
    handle_label = HandleLabel(handle_label_str)
    
    return NodeID(node_id), handle_label, direction