"""Simplified execution view for local execution.

DEPRECATED: This module has been moved to dipeo.application.engine.
Please update your imports to use the new location.
"""

import warnings
from dipeo.application.engine import LocalExecutionView, NodeView, EdgeView

warnings.warn(
    "Importing from dipeo_application.execution_view "
    "is deprecated. Please import from dipeo.application.engine instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["LocalExecutionView", "NodeView", "EdgeView"]
