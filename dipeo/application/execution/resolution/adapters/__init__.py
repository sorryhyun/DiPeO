"""Input resolution implementations and adapters.

This module contains:
- StandardRuntimeInputResolver: The primary implementation of runtime input resolution
- TypedInputResolutionServiceAdapter: Adapter for backward compatibility with old service
- Various adapters for bridging between old and new data structures
"""

from .input_resolution_adapter import (
    ExecutionContextAdapter,
    StandardRuntimeInputResolver,
    TypedInputResolutionServiceAdapter,
)

from .compile_time_adapter import (
    CompileTimeResolverAdapter,
    ExecutableNodeAdapter,
    EdgeAdapter,
)

__all__ = [
    # Runtime adapters
    "ExecutionContextAdapter",
    "StandardRuntimeInputResolver", 
    "TypedInputResolutionServiceAdapter",
    
    # Compile-time adapters
    "CompileTimeResolverAdapter",
    "ExecutableNodeAdapter",
    "EdgeAdapter",
]