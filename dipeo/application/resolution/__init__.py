# Diagram resolution pipeline for transforming DomainDiagram to ExecutableDiagram.
# Handles resolution, arrow transformation, execution order, and validation.

from .interface_based_compiler import InterfaceBasedDiagramCompiler
from .compile_time_resolver import StandardCompileTimeResolver
from .runtime_input_resolver import StandardRuntimeInputResolver, ExecutionContext
from .input_resolution import (
    Connection,
    TransformRules,
    CompileTimeResolver,
    RuntimeInputResolver,
    TransformationEngine,
)

# Compatibility imports for migration
from .simple_order_calculator import SimpleOrderCalculator
# Keep old name for compatibility during migration
ExecutionOrderCalculator = SimpleOrderCalculator

__all__ = [
    "ExecutionOrderCalculator",
    "InterfaceBasedDiagramCompiler",
    "StandardCompileTimeResolver",
    "StandardRuntimeInputResolver",
    "ExecutionContext",
    "SimpleOrderCalculator",
    # Base abstractions
    "Connection",
    "TransformRules",
    "CompileTimeResolver",
    "RuntimeInputResolver",
    "TransformationEngine",
]