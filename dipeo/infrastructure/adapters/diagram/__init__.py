"""Infrastructure adapters for diagram operations.

This module provides adapters that implement domain ports using
existing infrastructure implementations.
"""

from dipeo.infrastructure.adapters.diagram.compiler_adapter import (
    StandardCompilerAdapter,
    CachingCompilerAdapter,
    ValidatingCompilerAdapter,
)

from dipeo.infrastructure.adapters.diagram.serializer_adapter import (
    UnifiedSerializerAdapter,
    FormatStrategyAdapter,
    CachingSerializerAdapter,
)

from dipeo.infrastructure.adapters.diagram.resolution_adapter import (
    StandardCompileTimeResolverAdapter,
    StandardRuntimeResolverAdapter,
    StandardTransformationEngineAdapter,
    CompositeResolverAdapter,
    CachingRuntimeResolverAdapter,
)

__all__ = [
    # Compiler Adapters
    "StandardCompilerAdapter",
    "CachingCompilerAdapter",
    "ValidatingCompilerAdapter",
    # Serializer Adapters
    "UnifiedSerializerAdapter",
    "FormatStrategyAdapter",
    "CachingSerializerAdapter",
    # Resolution Adapters
    "StandardCompileTimeResolverAdapter",
    "StandardRuntimeResolverAdapter",
    "StandardTransformationEngineAdapter",
    "CompositeResolverAdapter",
    "CachingRuntimeResolverAdapter",
]