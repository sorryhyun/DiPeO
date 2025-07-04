"""DiPeO diagram converters and utilities."""

from .base import DiagramConverter, FormatStrategy
from .conversion_utils import backend_to_graphql, graphql_to_backend, BackendDiagram
from .shared_components import (
    ArrowBuilder,
    HandleGenerator,
    PositionCalculator,
    build_node,
    coerce_to_dict,
    ensure_position,
    extract_common_arrows,
)
from .strategies import (
    BaseConversionStrategy,
    NativeJsonStrategy,
    LightYamlStrategy,
    ReadableYamlStrategy,
)
from .unified_converter import UnifiedDiagramConverter, converter_registry

__all__ = [
    # Base classes
    "DiagramConverter",
    "FormatStrategy",
    "BaseConversionStrategy",
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
    "ArrowBuilder",
    # Models
    "BackendDiagram",
    # Utils
    "backend_to_graphql",
    "graphql_to_backend",
    "build_node",
    "coerce_to_dict",
    "ensure_position",
    "extract_common_arrows",
]
