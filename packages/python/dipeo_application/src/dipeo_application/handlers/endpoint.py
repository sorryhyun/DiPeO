"""Endpoint node handler - passes through data and optionally saves to file.

DEPRECATED: This module has been moved to dipeo.application.handlers.
Please update your imports to use the new location.
"""

import warnings
from dipeo.application.handlers import EndpointNodeHandler

warnings.warn(
    "Importing EndpointNodeHandler from dipeo_application.handlers.endpoint "
    "is deprecated. Please import from dipeo.application.handlers instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["EndpointNodeHandler"]