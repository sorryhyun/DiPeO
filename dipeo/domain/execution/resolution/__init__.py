"""Domain-level input resolution for node execution.

This package contains all business logic for resolving node inputs during execution.
The application layer should only orchestrate these domain functions.
"""

from .api import resolve_inputs
from .errors import (
    ResolutionError,
    InputResolutionError,
    TransformationError,
    SpreadCollisionError,
)

__all__ = [
    "resolve_inputs",
    "ResolutionError",
    "InputResolutionError",
    "TransformationError",
    "SpreadCollisionError",
]