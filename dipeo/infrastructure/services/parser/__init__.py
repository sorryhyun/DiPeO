"""Parser service module - DEPRECATED.

Import from dipeo.infrastructure.diagram.drivers instead.
"""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.diagram.drivers instead of dipeo.infrastructure.services.parser",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.diagram.drivers.parser_service import ParserService, get_parser_service

__all__ = [
    "ParserService",
    "get_parser_service",
]