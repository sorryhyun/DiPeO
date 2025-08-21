"""Domain-level input resolution for node execution.

This package contains all business logic for resolving node inputs during execution.
The application layer should only orchestrate these domain functions.
"""

from .api import resolve_inputs
from .errors import (
    ResolutionError,
    InputResolutionError,
    TransformationError,
    SpreadCollisionError,
)
from .runtime_resolver import RuntimeInputResolver
from .transformation_engine import (
    TransformationEngine,
    StandardTransformationEngine,
)
from .node_strategies import (
    NodeTypeStrategy,
    NodeTypeStrategyRegistry,
    BaseNodeTypeStrategy,
    PersonJobNodeStrategy,
    ConditionNodeStrategy,
    CollectNodeStrategy,
    create_default_strategy_registry,
)
from .data_structures import (
    InputResolutionContext,
    TransformationContext,
    ValidationResult,
    ResolutionPath,
    ResolutionStep,
)

__all__ = [
    # API
    "resolve_inputs",
    # Errors
    "ResolutionError",
    "InputResolutionError",
    "TransformationError",
    "SpreadCollisionError",
    # Runtime Resolution
    "RuntimeInputResolver",
    # Transformation
    "TransformationEngine",
    "StandardTransformationEngine",
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