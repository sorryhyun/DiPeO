"""Infrastructure adapters for diagram operations.

This module provides adapters that implement domain ports using
existing infrastructure implementations.
"""

from .compiler_adapter import (
    StandardCompilerAdapter,
    CachingCompilerAdapter,
    ValidatingCompilerAdapter,
)

from .serializer_adapter import (
    UnifiedSerializerAdapter,
    FormatStrategyAdapter,
    CachingSerializerAdapter,
)

# Resolution adapters removed - use domain implementations directly

__all__ = [
    # Compiler Adapters
    "StandardCompilerAdapter",
    "CachingCompilerAdapter",
    "ValidatingCompilerAdapter",
    # Serializer Adapters
    "UnifiedSerializerAdapter",
    "FormatStrategyAdapter",
    "CachingSerializerAdapter",
    # Resolution adapters removed - use domain implementations directly
]