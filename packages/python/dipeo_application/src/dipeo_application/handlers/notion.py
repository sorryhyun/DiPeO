"""Notion node handler - integrates with Notion API."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.handlers.notion is deprecated. "
    "Use dipeo.application.handlers.notion instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.handlers.notion import NotionNodeHandler

__all__ = ["NotionNodeHandler"]