"""Backward compatibility adapters for input resolution refactoring.

These adapters allow the existing code to gradually migrate to the new
interface-based approach without breaking changes.
"""

from .input_resolution_adapter import (
    ExecutionContextAdapter,
    RuntimeInputResolverAdapter,
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
    "RuntimeInputResolverAdapter", 
    "TypedInputResolutionServiceAdapter",
    
    # Compile-time adapters
    "CompileTimeResolverAdapter",
    "ExecutableNodeAdapter",
    "EdgeAdapter",
]