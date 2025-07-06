"""Minimal message router service."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.services.minimal_message_router is deprecated. "
    "Use dipeo.application.services.minimal_message_router instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.services.minimal_message_router import MinimalMessageRouter

__all__ = ["MinimalMessageRouter"]