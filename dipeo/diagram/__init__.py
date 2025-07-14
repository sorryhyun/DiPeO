"""DiPeO diagram converters and utilities."""

from .base import DiagramConverter, FormatStrategy
from .conversion_utils import dict_to_domain_diagram, domain_diagram_to_dict
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
    LightYamlStrategy,
    NativeJsonStrategy,
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
    # Utils
    "dict_to_domain_diagram",
    "domain_diagram_to_dict",
    "build_node",
    "coerce_to_dict",
    "ensure_position",
    "extract_common_arrows",
]
