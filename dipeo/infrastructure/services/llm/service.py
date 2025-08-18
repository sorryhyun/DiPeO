"""Backward compatibility for llm service - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.llm.drivers.service instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.llm.drivers.service import *