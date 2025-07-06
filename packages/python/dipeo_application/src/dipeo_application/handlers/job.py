"""Job node handler - base job execution handler."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.handlers.job is deprecated. "
    "Use dipeo.application.handlers.job instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.handlers.job import JobNodeHandler

__all__ = ["JobNodeHandler"]