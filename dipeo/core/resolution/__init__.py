"""Input resolution interfaces for clean separation of concerns.

This package defines the interfaces that enable:
- Clear boundaries between compile-time and runtime resolution
- Unified data structures for edges and outputs
- Strategy pattern for node-type-specific behavior
- Pluggable transformation engine
"""

# Import from core execution for moved classes
from dipeo.core.compilation.executable_diagram import (
    ExecutableEdgeV2,
    NodeOutputProtocolV2,
    StandardNodeOutput,
)
# Import remaining classes from data_structures
from .data_structures import (
    EdgeMetadata,
    OutputExtractor,
    TransformationContext,
)
from .node_strategies import (
    ApplicationNodeStrategy,
    ConditionStrategy,
    DefaultStrategy,
    NodeStrategyFactory,
    PersonJobStrategy,
)
# Import base resolution interfaces
from .interfaces import (
    CompileTimeResolver,
    Connection,
    RuntimeInputResolver,
    TransformRules,
    TransformationEngine,
)
from .transformation_engine import (
    BranchOnCondition,
    ContentTypeConverter,
    ExtractToolResults,
    Formatter,
    StandardTransformationEngine,
    TransformationEngine,
    TransformationRule,
    VariableExtractor,
)

__all__ = [
    # Transformation engine
    "BranchOnCondition",
    # Resolvers
    "CompileTimeResolver",
    # Node strategies  
    "ConditionStrategy",
    # Resolvers
    "Connection",
    # Transformation engine
    "ContentTypeConverter",
    # Node strategies
    "DefaultStrategy",
    # Data structures
    "EdgeMetadata",
    # Data structures
    "ExecutableEdgeV2",
    # Transformation engine
    "ExtractToolResults",
    # Transformation engine
    "Formatter",
    # Node strategies
    "NodeStrategyFactory",
    # Data structures
    "NodeOutputProtocolV2",
    # Node strategies
    "ApplicationNodeStrategy",
    # Data structures
    "OutputExtractor",
    # Node strategies
    "PersonJobStrategy",
    # Resolvers
    "RuntimeInputResolver",
    # Data structures
    "StandardNodeOutput",
    # Transformation engine
    "StandardTransformationEngine",
    # Data structures
    "TransformationContext",
    # Transformation engine
    "TransformationEngine",
    # Transformation engine
    "TransformationRule",
    # Resolvers
    "TransformRules",
    # Transformation engine
    "VariableExtractor",
]