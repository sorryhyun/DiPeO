"""Domain resolution system for input resolution and transformation.

This module provides the domain-owned contracts and abstractions for
resolving inputs during diagram compilation and execution.
"""

from dipeo.domain.resolution.interfaces import (
    Connection,
    TransformRules,
    CompileTimeResolver,
    RuntimeInputResolver,
    TransformationEngine,
    CompileTimeResolverV2,
    RuntimeInputResolverV2,
    TransformationEngineV2,
)

from dipeo.domain.resolution.node_strategies import (
    NodeTypeStrategy,
    NodeTypeStrategyRegistry,
    BaseNodeTypeStrategy,
    PersonJobNodeStrategy,
    ConditionNodeStrategy,
    CollectNodeStrategy,
    create_default_strategy_registry,
)

from dipeo.domain.resolution.data_structures import (
    InputResolutionContext,
    TransformationContext,
    ValidationResult,
    ResolutionPath,
    ResolutionStep,
)

__all__ = [
    # Interfaces
    "Connection",
    "TransformRules",
    "CompileTimeResolver",
    "RuntimeInputResolver",
    "TransformationEngine",
    "CompileTimeResolverV2",
    "RuntimeInputResolverV2", 
    "TransformationEngineV2",
    # Node Strategies
    "NodeTypeStrategy",
    "NodeTypeStrategyRegistry",
    "BaseNodeTypeStrategy",
    "PersonJobNodeStrategy",
    "ConditionNodeStrategy",
    "CollectNodeStrategy",
    "create_default_strategy_registry",
    # Data Structures
    "InputResolutionContext",
    "TransformationContext",
    "ValidationResult",
    "ResolutionPath",
    "ResolutionStep",
]