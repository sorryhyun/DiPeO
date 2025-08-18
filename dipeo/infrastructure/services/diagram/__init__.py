"""Backward compatibility for diagram services - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.diagram.drivers instead of dipeo.infrastructure.services.diagram",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.diagram.drivers import *