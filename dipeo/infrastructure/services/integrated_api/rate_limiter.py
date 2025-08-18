"""Backward compatibility for rate_limiter - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.integrations.drivers.integrated_api.rate_limiter instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.integrations.drivers.integrated_api.rate_limiter import *