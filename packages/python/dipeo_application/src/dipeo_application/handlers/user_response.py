"""User response node handler - handles interactive user input."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.handlers.user_response is deprecated. "
    "Use dipeo.application.handlers.user_response instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.handlers.user_response import UserResponseNodeHandler

__all__ = ["UserResponseNodeHandler"]