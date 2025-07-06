"""Unified execution controller for managing execution flow and state.

DEPRECATED: This module has been moved to dipeo.application.engine.
Please update your imports to use the new location.
"""

import warnings
from dipeo.application.engine import ExecutionController, NodeExecutionState

warnings.warn(
    "Importing from dipeo_application.execution_controller "
    "is deprecated. Please import from dipeo.application.engine instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["ExecutionController", "NodeExecutionState"]
