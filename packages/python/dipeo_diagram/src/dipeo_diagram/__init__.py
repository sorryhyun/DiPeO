"""DiPeO Diagram - DEPRECATED: Use 'dipeo.diagram' or import from 'dipeo' directly.

This module is deprecated and will be removed in a future version.
Please update your imports:
  - Change 'from dipeo_diagram import X' to 'from dipeo.diagram import X'
  - Or preferably 'from dipeo import X' for commonly used exports
"""

import warnings

warnings.warn(
    "The 'dipeo_diagram' package is deprecated. "
    "Please use 'from dipeo.diagram import ...' or 'from dipeo import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from the new location for backward compatibility
from dipeo.diagram import (
    # Base classes
    DiagramConverter,
    FormatStrategy,
    BaseConversionStrategy,
    # Converter
    UnifiedDiagramConverter,
    # Registry
    converter_registry,
    # Strategies
    NativeJsonStrategy,
    LightYamlStrategy,
    ReadableYamlStrategy,
    # Components
    HandleGenerator,
    PositionCalculator,
    ArrowBuilder,
    # Models
    BackendDiagram,
    # Utils
    backend_to_graphql,
    graphql_to_backend,
    build_node,
    coerce_to_dict,
    ensure_position,
    extract_common_arrows,
)

# Re-export submodules
from dipeo.diagram import base
from dipeo.diagram import conversion_utils
from dipeo.diagram import shared_components
from dipeo.diagram import strategies
from dipeo.diagram import unified_converter

__version__ = "0.1.0"

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
    # Submodules
    "base",
    "conversion_utils",
    "shared_components",
    "strategies",
    "unified_converter",
]