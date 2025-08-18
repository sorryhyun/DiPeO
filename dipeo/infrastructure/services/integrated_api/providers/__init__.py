"""Backward compatibility for providers - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.integrations.drivers.integrated_api.providers instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.integrations.drivers.integrated_api.providers import *