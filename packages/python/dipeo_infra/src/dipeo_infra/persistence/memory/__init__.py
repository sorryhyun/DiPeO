"""Memory persistence adapters."""

import warnings

warnings.warn(
    "Importing from dipeo_infra.persistence.memory is deprecated. "
    "Use dipeo.infra.persistence.memory instead.",
    DeprecationWarning,
    stacklevel=2
)

from .memory_service import MemoryService

__all__ = ["MemoryService"]
