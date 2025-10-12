"""Core operations for diagram domain objects (handles, nodes, arrows)."""

from .arrow_operations import (
    ArrowBuilder,
    ArrowIdGenerator,
    arrows_list_to_dict,
    create_arrow_dict,
)
from .handle_operations import (
    HandleIdOperations,
    HandleLabelParser,
    HandleReference,
    HandleValidator,
    ParsedHandle,
)
from .node_operations import (
    NodeDictionaryBuilder,
    nodes_list_to_dict,
)

__all__ = [
    # Arrow operations
    "ArrowBuilder",
    "ArrowIdGenerator",
    # Handle operations
    "HandleIdOperations",
    "HandleLabelParser",
    "HandleReference",
    "HandleValidator",
    # Node operations
    "NodeDictionaryBuilder",
    "ParsedHandle",
    "arrows_list_to_dict",
    "create_arrow_dict",
    "nodes_list_to_dict",
]
