"""Backward compatibility for database service - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.shared.database.service instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.shared.database.service import *