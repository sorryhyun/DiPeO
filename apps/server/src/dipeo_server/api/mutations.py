"""Combined mutations for GraphQL schema."""
import strawberry

from .node_mutation import NodeMutations
from .arrow_mutation import ArrowMutations
from .handle_mutation import HandleMutations
from .person_mutation import PersonMutations
from .api_key_mutation import ApiKeyMutations
from .diagram_mutation import DiagramMutations
from .execution_mutation import ExecutionMutations
from .upload_mutation import UploadMutations
from .utility_mutation import UtilityMutations


@strawberry.type
class Mutation(
    NodeMutations,
    ArrowMutations,
    HandleMutations,
    PersonMutations,
    ApiKeyMutations,
    DiagramMutations,
    ExecutionMutations,
    UploadMutations,
    UtilityMutations
):
    """Root mutation type combining all mutations."""
    pass