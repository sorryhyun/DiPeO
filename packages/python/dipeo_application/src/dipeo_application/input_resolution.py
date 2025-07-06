"""Simplified input resolution strategies for NodeView.

DEPRECATED: This module has been moved to dipeo.application.utils.
Please update your imports to use the new location.
"""

import warnings
from dipeo.application.utils import get_active_inputs_simplified

warnings.warn(
    "Importing from dipeo_application.input_resolution "
    "is deprecated. Please import from dipeo.application.utils instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["get_active_inputs_simplified"]