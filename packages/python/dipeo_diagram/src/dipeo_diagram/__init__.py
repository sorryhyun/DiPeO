"""DiPeO diagram converters and utilities."""

from .base import DiagramConverter, FormatStrategy
from .conversion_utils import backend_to_graphql, graphql_to_backend
from .models import BackendDiagram, FileInfo, ReadableFlow
from .shared_components import (
    ArrowBuilder,
    HandleGenerator,
    NodeTypeMapper,
    PositionCalculator,
    build_node,
    coerce_to_dict,
    ensure_position,
    extract_common_arrows,
)
from .strategies import LightYamlStrategy, NativeJsonStrategy, ReadableYamlStrategy
from .unified_converter import UnifiedDiagramConverter
from .registry import converter_registry

__all__ = [
    # Base classes
    "DiagramConverter",
    "FormatStrategy",
    # Converter
    "UnifiedDiagramConverter",
    # Registry
    "converter_registry",
    # Strategies
    "NativeJsonStrategy",
    "LightYamlStrategy",
    "ReadableYamlStrategy",
    # Components
    "HandleGenerator",
    "PositionCalculator",
    "NodeTypeMapper",
    "ArrowBuilder",
    # Models
    "BackendDiagram",
    "FileInfo",
    "ReadableFlow",
    # Utils
    "backend_to_graphql",
    "graphql_to_backend",
    "build_node",
    "coerce_to_dict",
    "ensure_position",
    "extract_common_arrows",
]