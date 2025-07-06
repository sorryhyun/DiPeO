"""DEPRECATED: This module has been moved to dipeo.container.providers"""

import warnings

warnings.warn(
    "dipeo_container.providers is deprecated. Please use dipeo.container.providers instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from new location
from dipeo.container.providers import *