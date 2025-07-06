"""
Application implementation of ExecutionContextPort.

DEPRECATED: This module has been moved to dipeo.application.context.
Please update your imports to use the new location.
"""

import warnings
from dipeo.application.context import ApplicationExecutionContext

warnings.warn(
    "Importing ApplicationExecutionContext from dipeo_application.execution_context "
    "is deprecated. Please import from dipeo.application.context instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["ApplicationExecutionContext"]