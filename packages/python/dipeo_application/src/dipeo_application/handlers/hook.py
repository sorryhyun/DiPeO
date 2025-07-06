"""Hook node handler for executing external hooks within diagram flow."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.handlers.hook is deprecated. "
    "Use dipeo.application.handlers.hook instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.handlers.hook import HookNodeHandler

__all__ = ["HookNodeHandler"]