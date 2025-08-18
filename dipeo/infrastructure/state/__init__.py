"""Backward compatibility for state infrastructure - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.execution.state instead of dipeo.infrastructure.state",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.execution.state import *