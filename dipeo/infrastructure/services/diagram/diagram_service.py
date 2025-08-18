"""Backward compatibility for diagram_service - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.diagram.drivers.diagram_service instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.diagram.drivers.diagram_service import *