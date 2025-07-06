"""Template utilities."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.utils.template is deprecated. "
    "Use dipeo.application.utils.template instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.utils.template import *

__all__ = ["substitute_template"]