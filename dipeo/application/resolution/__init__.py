# Diagram resolution pipeline for transforming DomainDiagram to ExecutableDiagram.
# Handles resolution, arrow transformation, execution order, and validation.

from .arrow_transformer import ArrowTransformer
from .compiler import NodeFactory
from .handle_resolver import HandleResolver
from .static_diagram_compiler import StaticDiagramCompiler

# Compatibility imports for migration
from .simple_order_calculator import SimpleOrderCalculator
# Keep old name for compatibility during migration
ExecutionOrderCalculator = SimpleOrderCalculator

__all__ = [
    "ArrowTransformer",
    "ExecutionOrderCalculator",
    "HandleResolver",
    "NodeFactory",
    "StaticDiagramCompiler"
]