"""Conversions generator module."""

from .conversions_generator import (
    extract_node_type_map,
    generate_conversions,
    # Backward compatibility
    main
)

__all__ = ['extract_node_type_map', 'generate_conversions', 'main']