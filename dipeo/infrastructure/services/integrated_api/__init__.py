"""Backward compatibility for integrated_api - DEPRECATED.

Import from dipeo.infrastructure.integrations.drivers.integrated_api instead.
"""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.integrations.drivers.integrated_api instead of dipeo.infrastructure.services.integrated_api",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from new location
from dipeo.infrastructure.integrations.drivers.integrated_api import *
from dipeo.infrastructure.integrations.drivers.integrated_api.manifest_schema import *
from dipeo.infrastructure.integrations.drivers.integrated_api.registry import *
from dipeo.infrastructure.integrations.drivers.integrated_api.service import *
from dipeo.infrastructure.integrations.drivers.integrated_api.generic_provider import *
from dipeo.infrastructure.integrations.drivers.integrated_api.auth_strategies import *
from dipeo.infrastructure.integrations.drivers.integrated_api.rate_limiter import *