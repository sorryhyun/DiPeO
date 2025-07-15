"""Integration domain services - Deprecated, use new locations instead."""

import warnings

# Import from new locations
from dipeo.domain.api.services import APIValidator

from .data_transformer import DataTransformer  # Already a wrapper to utils

warnings.warn(
    "dipeo.domain.services.integration is deprecated. "
    "Use dipeo.domain.api.services for APIValidator and "
    "dipeo.utils.transform for DataTransformer.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    'APIValidator',
    'DataTransformer',
]