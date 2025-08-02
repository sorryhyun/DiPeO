# Diagram resolution pipeline for transforming DomainDiagram to ExecutableDiagram.
# Handles resolution, arrow transformation, execution order, and validation.

from dipeo.application.execution.resolution.adapters.arrow_transformer import ArrowTransformer
from .compiler import NodeFactory
from dipeo.application.execution.resolution.adapters.handle_resolver import HandleResolver
from .interface_based_compiler import InterfaceBasedDiagramCompiler

# Compatibility imports for migration
from .simple_order_calculator import SimpleOrderCalculator
# Keep old name for compatibility during migration
ExecutionOrderCalculator = SimpleOrderCalculator

__all__ = [
    "ExecutionOrderCalculator",
    "NodeFactory",
    "InterfaceBasedDiagramCompiler"
]