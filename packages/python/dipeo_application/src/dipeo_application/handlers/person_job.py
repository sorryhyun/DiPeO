"""Simplified person_job handler with direct implementation."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.handlers.person_job is deprecated. "
    "Use dipeo.application.handlers.person_job instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.handlers.person_job import PersonJobNodeHandler

__all__ = ["PersonJobNodeHandler"]