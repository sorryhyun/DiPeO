"""Backward compatibility for messaging adapters - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.execution.messaging instead of dipeo.infrastructure.adapters.messaging",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.execution.messaging import *