"""Diagram bounded context in application layer.

This module handles:
- Diagram compilation and validation
- Diagram serialization and deserialization
- Input resolution (compile-time and runtime)
- GraphQL resolvers for diagram operations
"""

from .wiring import wire_diagram

__all__ = ["wire_diagram"]