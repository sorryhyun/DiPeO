"""Unified execution engine that simplifies the two-phase execution model.

DEPRECATED: This module has been moved to dipeo.application.engine.
Please update your imports to use the new location.
"""

import warnings
from dipeo.application.engine import ExecutionEngine

warnings.warn(
    "Importing ExecutionEngine from dipeo_application.execution_engine "
    "is deprecated. Please import from dipeo.application.engine instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["ExecutionEngine"]