"""Backward compatibility for database services - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.shared.database instead of dipeo.infrastructure.services.database",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.shared.database import *