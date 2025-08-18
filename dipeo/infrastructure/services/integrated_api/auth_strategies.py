"""Backward compatibility for auth_strategies - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.integrations.drivers.integrated_api.auth_strategies instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.integrations.drivers.integrated_api.auth_strategies import *