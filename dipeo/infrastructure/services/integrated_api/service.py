"""Backward compatibility for service - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.integrations.drivers.integrated_api.service instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.integrations.drivers.integrated_api.service import *