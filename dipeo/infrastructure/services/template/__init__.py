"""Backward compatibility for template services - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.shared.template.drivers instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.shared.template.drivers import *