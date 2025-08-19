"""Domain diagram validation service."""

from .service import (
    collect_diagnostics,
    validate_diagram,
    validate_structure_only,
    validate_connections,
)

__all__ = [
    "collect_diagnostics",
    "validate_diagram",
    "validate_structure_only",
    "validate_connections",
]