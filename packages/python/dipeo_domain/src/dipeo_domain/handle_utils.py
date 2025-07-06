"""
Handle ID utilities for managing handle IDs.
This is a manually maintained file, not auto-generated.

Provides a single source of truth for handle ID parsing and creation.
"""

from typing import Tuple, Optional, NamedTuple
from dipeo_domain import HandleID, NodeID, HandleDirection, HandleLabel


class ParsedHandle(NamedTuple):
    """Parsed handle components for efficient access."""
    node_id: NodeID
    handle_label: HandleLabel
    direction: HandleDirection


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
    
    Format: [nodeId]_[handleLabel]_[direction]
    Example: 'node_123_default_output' -> ('node_123', 'default', 'output')
    """
    parts = handle_id.split('_')
    if len(parts) < 3:
        raise ValueError(f"Invalid handle ID format: {handle_id}. Expected format: nodeId_handleLabel_direction")
    
    # Extract parts from the end (direction and label are always last)
    direction_str = parts[-1]
    handle_label_str = parts[-2]
    node_id_parts = parts[:-2]
    node_id = '_'.join(node_id_parts)
    
    if not node_id:
        raise ValueError(f"Invalid handle ID format: {handle_id}. Node ID cannot be empty")
    
    # Validate direction
    try:
        direction = HandleDirection(direction_str)
    except ValueError:
        raise ValueError(f"Invalid direction '{direction_str}' in handle ID: {handle_id}")
    
    # Validate handle label
    try:
        handle_label = HandleLabel(handle_label_str)
    except ValueError:
        # Allow custom handle labels for DB nodes
        handle_label = HandleLabel(handle_label_str)
    
    return NodeID(node_id), handle_label, direction


def parse_handle_id_safe(
    handle_id: HandleID
) -> Optional[ParsedHandle]:
    """Parse a handle ID safely, returning None on invalid format."""
    try:
        node_id, handle_label, direction = parse_handle_id(handle_id)
        return ParsedHandle(node_id, handle_label, direction)
    except ValueError:
        return None


def extract_node_id_from_handle(handle_id: HandleID) -> Optional[NodeID]:
    """Extract just the node ID from a handle ID.
    
    This is a convenience function for cases where only the node ID is needed.
    Returns None if the handle ID is invalid.
    """
    parsed = parse_handle_id_safe(handle_id)
    return parsed.node_id if parsed else None


def is_valid_handle_id(handle_id: str) -> bool:
    """Check if a string is a valid handle ID."""
    return parse_handle_id_safe(HandleID(handle_id)) is not None