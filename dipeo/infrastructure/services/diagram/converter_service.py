"""Backward compatibility for converter_service - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.diagram.drivers.converter_service instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.diagram.drivers.converter_service import *