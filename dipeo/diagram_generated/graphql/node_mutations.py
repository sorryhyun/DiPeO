







"""
Strawberry GraphQL mutations for DiPeO nodes.
Generated automatically from node specifications.

Generated at: 2025-08-19T00:00:38.736895
"""

import strawberry
from typing import *
from strawberry.types import *

# Import data types and unions
from .strawberry_nodes import *

# Import base types
from dipeo.application.graphql.types.domain_types import *
from dipeo.application.graphql.types.inputs import *

# Import services and keys
from dipeo.application.registry import *
from dipeo.application.registry.keys import *


# Generate input types for each node



@strawberry.type
class NodeMutations:
    """Type-safe mutations for node operations"""
    



# Export mutations
__all__ = [
    'NodeMutations',

]