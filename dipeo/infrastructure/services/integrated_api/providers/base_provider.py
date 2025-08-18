"""Backward compatibility for base_provider - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.integrations.drivers.integrated_api.providers.base_provider instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.integrations.drivers.integrated_api.providers.base_provider import *