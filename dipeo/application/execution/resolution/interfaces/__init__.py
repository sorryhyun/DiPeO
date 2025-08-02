"""Input resolution interfaces for clean separation of concerns.

This package defines the interfaces that enable:
- Clear boundaries between compile-time and runtime resolution
- Unified data structures for edges and outputs
- Strategy pattern for node-type-specific behavior
- Pluggable transformation engine
"""

from .data_structures import (
    EdgeMetadata,
    ExecutableEdgeV2,
    NodeOutputProtocolV2,
    OutputExtractor,
    StandardNodeOutput,
    TransformationContext,
)
from .node_strategies import (
    ConditionStrategy,
    DefaultStrategy,
    ExecutionContextProtocol,
    NodeStrategyFactory,
    NodeTypeStrategy,
    PersonJobStrategy,
)
from .resolvers import (
    CompileTimeResolver,
    Connection,
    ExecutionContext,
    RuntimeInputResolver,
    TransformRules,
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
    # Resolvers
    "ExecutionContext",
    # Node strategies
    "ExecutionContextProtocol",
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
    "NodeTypeStrategy",
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