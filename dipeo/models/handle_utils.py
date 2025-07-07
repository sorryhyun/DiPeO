"""
Handle ID utilities for managing handle IDs.
This is a manually maintained file, not auto-generated.

Provides a single source of truth for handle ID parsing and creation.
"""

from typing import Tuple, Optional, NamedTuple, Dict
from .models import HandleID, NodeID, HandleDirection, HandleLabel


class ParsedHandle(NamedTuple):
    """Parsed handle components for efficient access."""
    node_id: NodeID
    handle_label: HandleLabel
    direction: HandleDirection


class HandleReference:
    """Handle reference with cached parsed components for performance.
    
    This class provides efficient access to handle components by parsing
    the handle ID once and caching the results. Use this for frequently
    accessed handles in hot paths like edge traversal.
    """
    
    # Class-level cache for handle references
    _cache: Dict[HandleID, 'HandleReference'] = {}
    
    def __init__(self, handle_id: HandleID):
        """Initialize handle reference with cached parsing."""
        self.handle_id = handle_id
        self._parsed: Optional[ParsedHandle] = None
        self._parse_error: Optional[str] = None
        
        # Parse immediately to cache result
        self._ensure_parsed()
    
    def _ensure_parsed(self) -> None:
        """Parse handle ID if not already parsed."""
        if self._parsed is None and self._parse_error is None:
            try:
                node_id, handle_label, direction = parse_handle_id(self.handle_id)
                self._parsed = ParsedHandle(node_id, handle_label, direction)
            except ValueError as e:
                self._parse_error = str(e)
    
    @property
    def node_id(self) -> NodeID:
        """Get node ID from handle."""
        if self._parsed:
            return self._parsed.node_id
        raise ValueError(f"Invalid handle ID: {self._parse_error}")
    
    @property
    def handle_label(self) -> HandleLabel:
        """Get handle label from handle."""
        if self._parsed:
            return self._parsed.handle_label
        raise ValueError(f"Invalid handle ID: {self._parse_error}")
    
    @property
    def direction(self) -> HandleDirection:
        """Get direction from handle."""
        if self._parsed:
            return self._parsed.direction
        raise ValueError(f"Invalid handle ID: {self._parse_error}")
    
    @property
    def is_valid(self) -> bool:
        """Check if handle ID is valid."""
        return self._parsed is not None
    
    @classmethod
    def get_or_create(cls, handle_id: HandleID) -> 'HandleReference':
        """Get cached handle reference or create new one.
        
        This method ensures only one HandleReference instance exists per
        unique handle ID, reducing memory usage and parsing overhead.
        """
        if handle_id not in cls._cache:
            cls._cache[handle_id] = cls(handle_id)
        return cls._cache[handle_id]
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the handle reference cache.
        
        Use this when switching between diagrams or in tests.
        """
        cls._cache.clear()


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


__all__ = [
    'ParsedHandle',
    'HandleReference',
    'create_handle_id',
    'parse_handle_id',
    'parse_handle_id_safe',
    'extract_node_id_from_handle',
    'is_valid_handle_id',
]