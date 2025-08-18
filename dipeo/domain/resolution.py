"""Backward compatibility re-export for resolution module.

This module maintains backward compatibility for imports during the migration
of resolution from domain.resolution to domain.diagram.resolution.

DEPRECATED: Use dipeo.domain.diagram.resolution instead.
"""

# Re-export everything from the new location
from dipeo.domain.diagram.resolution import *
from dipeo.domain.diagram.resolution import (
    __all__ as _resolution_all,
    CompileTimeResolver,
    RuntimeInputResolver,
    RuntimeInputResolverV2,
    TransformationEngine,
    TransformationEngineV2,
    CompileTimeResolverV2,
    Connection,
    TransformRules,
)

# Re-export node strategies
from dipeo.domain.diagram.resolution.node_strategies import *

# Re-export data structures  
from dipeo.domain.diagram.resolution.data_structures import *

# Re-export interfaces
from dipeo.domain.diagram.resolution.interfaces import *

# Try to import transformation engine if it exists
try:
    from dipeo.domain.diagram.resolution.transformation_engine import (
        StandardTransformationEngine,
    )
except ImportError:
    pass

__all__ = [
    "CompileTimeResolver",
    "RuntimeInputResolver", 
    "RuntimeInputResolverV2",
    "TransformationEngine",
    "TransformationEngineV2",
    "CompileTimeResolverV2",
    "Connection",
    "TransformRules",
    "StandardTransformationEngine",
]