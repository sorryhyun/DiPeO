"""Domain-level input resolution for node execution.

This package contains all business logic for resolving node inputs during execution.
The application layer should only orchestrate these domain functions.
"""

from .api import resolve_inputs
from .data_structures import (
    InputResolutionContext,
    ResolutionPath,
    ResolutionStep,
    TransformationContext,
    ValidationResult,
)
from .errors import (
    InputResolutionError,
    ResolutionError,
    SpreadCollisionError,
    TransformationError,
)
from .node_strategies import (
    BaseNodeTypeStrategy,
    CollectNodeStrategy,
    ConditionNodeStrategy,
    NodeTypeStrategy,
    NodeTypeStrategyRegistry,
    PersonJobNodeStrategy,
    create_default_strategy_registry,
)
from .transformation_engine import (
    StandardTransformationEngine,
    TransformationEngine,
)

__all__ = [
    "BaseNodeTypeStrategy",
    "CollectNodeStrategy",
    "ConditionNodeStrategy",
    "InputResolutionContext",
    "InputResolutionError",
    "NodeTypeStrategy",
    "NodeTypeStrategyRegistry",
    "PersonJobNodeStrategy",
    "ResolutionError",
    "ResolutionPath",
    "ResolutionStep",
    "SpreadCollisionError",
    "StandardTransformationEngine",
    "TransformationContext",
    "TransformationEngine",
    "TransformationError",
    "ValidationResult",
    "create_default_strategy_registry",
    "resolve_inputs",
]
