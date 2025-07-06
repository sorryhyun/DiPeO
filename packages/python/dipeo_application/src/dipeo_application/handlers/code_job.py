"""Code job node handler - executes code in various environments."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.handlers.code_job is deprecated. "
    "Use dipeo.application.handlers.code_job instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.handlers.code_job import CodeJobNodeHandler

__all__ = ["CodeJobNodeHandler"]