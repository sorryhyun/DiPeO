"""Condition node handler - handles conditional logic in diagram execution."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.handlers.condition is deprecated. "
    "Use dipeo.application.handlers.condition instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.handlers.condition import ConditionNodeHandler

__all__ = ["ConditionNodeHandler"]