"""Start node handler - the kick-off point for diagram execution.

DEPRECATED: This module has been moved to dipeo.application.handlers.
Please update your imports to use the new location.
"""

import warnings
from dipeo.application.handlers import StartNodeHandler

warnings.warn(
    "Importing StartNodeHandler from dipeo_application.handlers.start "
    "is deprecated. Please import from dipeo.application.handlers instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["StartNodeHandler"]