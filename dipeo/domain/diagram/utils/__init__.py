"""Diagram utility modules."""

from .arrow_builder import (
    ArrowBuilder,
    ArrowIdGenerator,
    arrows_list_to_dict,
    create_arrow_dict,
)
from .conversion_utils import (
    _JsonMixin,
    _node_id_map,
    _YamlMixin,
)
from .data_extractors import DiagramDataExtractor
from .graph_utils import (
    count_node_connections,
    find_connected_nodes,
    find_edges_from,
    find_edges_to,
    find_orphan_nodes,
    is_dag,
)
from .handle_operations import (
    HandleIdOperations,
    HandleLabelParser,
    HandleReference,
    HandleValidator,
    ParsedHandle,
)
from .node_builder import (
    NodeDictionaryBuilder,
    nodes_list_to_dict,
)
from .node_field_mapper import NodeFieldMapper
from .person_extractor import PersonExtractor
from .person_resolver import PersonReferenceResolver
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
    # conversion_utils
    "_JsonMixin",
    "_YamlMixin",
    "_node_id_map",
    "arrows_list_to_dict",
    # shared_components
    "build_node",
    "coerce_to_dict",
    # graph_utils
    "count_node_connections",
    "create_arrow_dict",
    "create_node_id",
    "ensure_position",
    "extract_common_arrows",
    "find_connected_nodes",
    "find_edges_from",
    "find_edges_to",
    "find_orphan_nodes",
    "is_dag",
    "nodes_list_to_dict",
    # strategy_common
    "process_dotted_keys",
]
