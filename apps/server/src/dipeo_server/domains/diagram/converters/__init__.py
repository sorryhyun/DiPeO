"""
Diagram format converters for backend.
Uses unified converter with strategy pattern for all format conversions.
"""

from .base import DiagramConverter
from .diagram_format_converter import diagram_dict_to_graphql, graphql_to_diagram_dict
from .registry import converter_registry
from .strategies import (
    FormatStrategy,
    LightYamlStrategy,
    NativeJsonStrategy,
    ReadableYamlStrategy,
)
from .unified_converter import UnifiedDiagramConverter

__all__ = [
    "DiagramConverter",
    "FormatStrategy",
    "LightYamlStrategy",
    "NativeJsonStrategy",
    "ReadableYamlStrategy",
    "UnifiedDiagramConverter",
    "converter_registry",
    "diagram_dict_to_graphql",
    "graphql_to_diagram_dict",
]
