"""Diagram utility modules."""

from .arrow_builder import (
    ArrowBuilder,
    ArrowIdGenerator,
    arrows_list_to_dict,
    create_arrow_dict,
)
from .arrow_data_processor import ArrowDataProcessor  # deprecated - use arrow_builder
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

# Deprecated imports for backward compatibility
from .handle_parser import (
    HandleParser,
)
from .handle_utils import (
    create_handle_id,
    extract_node_id_from_handle,
    is_valid_handle_id,
    parse_handle_id,
    parse_handle_id_safe,
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
    # Arrow operations (new unified API)
    "ArrowBuilder",
    "ArrowDataProcessor",  # deprecated - use arrow_builder functions
    "ArrowIdGenerator",
    # Data extraction
    "DiagramDataExtractor",
    # Handle operations (new unified API)
    "HandleIdOperations",
    "HandleLabelParser",
    # Deprecated (for backward compatibility)
    "HandleParser",  # deprecated - use HandleLabelParser and HandleValidator
    "HandleReference",
    "HandleValidator",
    # Node operations (new unified API)
    "NodeDictionaryBuilder",
    "NodeFieldMapper",
    "ParsedHandle",
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
    "count_node_connections",
    "create_arrow_dict",
    "create_handle_id",  # deprecated - use HandleIdOperations.create_handle_id
    "create_node_id",
    "ensure_position",
    "extract_common_arrows",
    "extract_node_id_from_handle",  # deprecated - use HandleIdOperations.extract_node_id_from_handle
    "find_connected_nodes",
    # graph_utils
    "find_edges_from",
    "find_edges_to",
    "find_orphan_nodes",
    "is_dag",
    "is_valid_handle_id",  # deprecated - use HandleIdOperations.is_valid_handle_id
    "nodes_list_to_dict",
    "parse_handle_id",  # deprecated - use HandleIdOperations.parse_handle_id
    "parse_handle_id_safe",  # deprecated - use HandleIdOperations.parse_handle_id_safe
    "process_dotted_keys",
]
