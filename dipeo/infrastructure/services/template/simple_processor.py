"""Backward compatibility for simple_processor - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.shared.template.drivers.simple_processor instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.shared.template.drivers.simple_processor import *