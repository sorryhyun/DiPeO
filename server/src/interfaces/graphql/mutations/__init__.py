"""GraphQL mutation modules."""

from .diagram import DiagramMutations
from .node import NodeMutations
from .arrow import ArrowMutations
from .person import PersonMutations
from api_key import ApiKeyMutations
from .execution import ExecutionMutations
from .handle import HandleMutations
from .utility import UtilityMutations
from .upload import UploadMutations
from .diagram_file import DiagramFileMutations

# Import the main Mutation class from the parent module
import strawberry


@strawberry.type
class Mutation(
    DiagramMutations,
    NodeMutations,
    ArrowMutations,
    PersonMutations,
    ApiKeyMutations,
    ExecutionMutations,
    HandleMutations,
    UtilityMutations,
    UploadMutations,
    DiagramFileMutations
):
    """Root mutation type for DiPeO GraphQL API.
    
    This class composes all mutation types using multiple inheritance.
    All mutation methods are inherited from the respective domain-specific classes.
    """
    pass


__all__ = [
    'Mutation',
    'DiagramMutations',
    'NodeMutations',
    'ArrowMutations',
    'PersonMutations',
    'ApiKeyMutations',
    'ExecutionMutations',
    'HandleMutations',
    'UtilityMutations',
    'UploadMutations',
    'DiagramFileMutations',
]