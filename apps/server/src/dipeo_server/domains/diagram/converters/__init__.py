"""
Diagram format converters for backend.
Uses unified converter with strategy pattern for all format conversions.
"""

from .base import DiagramConverter, FormatStrategy
from .diagram_format_converter import backend_to_graphql, graphql_to_backend
from .registry import converter_registry
from .strategies import (
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
    "backend_to_graphql",
    "converter_registry",
    "graphql_to_backend",
]
