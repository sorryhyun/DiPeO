"""DEPRECATED: This module has been moved to dipeo.container.adapters"""

import warnings

warnings.warn(
    "dipeo_container.app_context_adapter is deprecated. Please use dipeo.container.adapters instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from new location
from dipeo.container.adapters import *