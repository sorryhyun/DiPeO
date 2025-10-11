"""Diagram utility modules.

Organized into subdirectories:
- core/: Core operations on diagram domain objects (handles, nodes, arrows)
- conversion/: Format conversion and data extraction utilities
- graph/: Graph traversal and analysis utilities
"""

from .conversion import (
    DiagramDataExtractor,
    _JsonMixin,
    _node_id_map,
    _YamlMixin,
    diagram_maps_to_arrays,
)
from .core import (
    ArrowBuilder,
    ArrowIdGenerator,
    HandleIdOperations,
    HandleLabelParser,
    HandleReference,
    HandleValidator,
    NodeDictionaryBuilder,
    ParsedHandle,
    arrows_list_to_dict,
    create_arrow_dict,
    nodes_list_to_dict,
)
from .graph import (
    count_node_connections,
    find_connected_nodes,
    find_edges_from,
    find_edges_to,
    find_orphan_nodes,
    is_dag,
)
from .node_field_mapper import NodeFieldMapper
from .person import PersonExtractor, PersonReferenceResolver, PersonValidator
from .shared_components import (
    build_node,
    coerce_to_dict,
    ensure_position,
    extract_common_arrows,
)
from .strategy_common import create_node_id, process_dotted_keys

__all__ = [
    # Arrow operations
    "ArrowBuilder",
    "ArrowIdGenerator",
    # Data extraction
    "DiagramDataExtractor",
    # Handle operations
    "HandleIdOperations",
    "HandleLabelParser",
    "HandleReference",
    "HandleValidator",
    # Node operations
    "NodeDictionaryBuilder",
    "NodeFieldMapper",
    "ParsedHandle",
    # Person operations
    "PersonExtractor",
    "PersonReferenceResolver",
    "PersonValidator",
    # Format converters
    "_JsonMixin",
    "_YamlMixin",
    "_node_id_map",
    "arrows_list_to_dict",
    # Shared components
    "build_node",
    "coerce_to_dict",
    # Graph operations
    "count_node_connections",
    "create_arrow_dict",
    "create_node_id",
    "diagram_maps_to_arrays",
    "ensure_position",
    "extract_common_arrows",
    "find_connected_nodes",
    "find_edges_from",
    "find_edges_to",
    "find_orphan_nodes",
    "is_dag",
    "nodes_list_to_dict",
    "process_dotted_keys",
]
