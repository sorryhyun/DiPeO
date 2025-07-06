"""Minimal state store service."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.services.minimal_state_store is deprecated. "
    "Use dipeo.application.services.minimal_state_store instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.services.minimal_state_store import MinimalStateStore

__all__ = ["MinimalStateStore"]