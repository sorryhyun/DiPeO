"""Backward compatibility shim for resolution interfaces.

DEPRECATED: This module is kept for backward compatibility.
Use dipeo.domain.resolution.interfaces instead.
"""

import warnings

# Import everything from the new location
from dipeo.domain.resolution.interfaces import (
    Connection,
    TransformRules,
    CompileTimeResolver,
    RuntimeInputResolver,
    TransformationEngine,
    CompileTimeResolverV2,
    RuntimeInputResolverV2,
    TransformationEngineV2,
)

# Re-export everything
__all__ = [
    "Connection",
    "TransformRules",
    "CompileTimeResolver",
    "RuntimeInputResolver",
    "TransformationEngine",
    "CompileTimeResolverV2",
    "RuntimeInputResolverV2",
    "TransformationEngineV2",
]

def _warn_deprecated():
    """Emit deprecation warning when this module is imported."""
    warnings.warn(
        "Importing from dipeo.core.resolution.interfaces is deprecated. "
        "Use dipeo.domain.resolution.interfaces instead.",
        DeprecationWarning,
        stacklevel=3
    )

# Warn on import
_warn_deprecated()