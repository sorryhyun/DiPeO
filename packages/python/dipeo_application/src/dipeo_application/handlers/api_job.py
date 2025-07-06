"""API job node handler - executes HTTP API calls."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.handlers.api_job is deprecated. "
    "Use dipeo.application.handlers.api_job instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.handlers.api_job import ApiJobNodeHandler

__all__ = ["ApiJobNodeHandler"]