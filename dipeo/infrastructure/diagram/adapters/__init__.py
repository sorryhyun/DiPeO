"""Infrastructure adapters for diagram operations.

This module provides adapters that implement domain ports using
existing infrastructure implementations.
"""

from .compiler_adapter import (
    CachingCompilerAdapter,
    StandardCompilerAdapter,
    ValidatingCompilerAdapter,
)
from .serializer_adapter import (
    CachingSerializerAdapter,
    FormatStrategyAdapter,
    UnifiedSerializerAdapter,
)

# Resolution adapters removed - use domain implementations directly

__all__ = [
    "CachingCompilerAdapter",
    "CachingSerializerAdapter",
    "FormatStrategyAdapter",
    # Compiler Adapters
    "StandardCompilerAdapter",
    # Serializer Adapters
    "UnifiedSerializerAdapter",
    "ValidatingCompilerAdapter",
    # Resolution adapters removed - use domain implementations directly
]
