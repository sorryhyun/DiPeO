"""Backward compatibility for parser_service - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.diagram.drivers.parser_service instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.diagram.drivers.parser_service import *