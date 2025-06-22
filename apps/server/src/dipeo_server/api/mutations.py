"""Combined mutations for GraphQL schema."""
import strawberry

from .node_mutation import NodeMutations
from .graph_element_mutations import GraphElementMutations
from .person_mutation import PersonMutations
from .api_key_mutation import ApiKeyMutations
from .diagram_mutation import DiagramMutations
from .execution_mutation import ExecutionMutations
from .upload_mutation import UploadMutations
from .utility_mutation import UtilityMutations


@strawberry.type
class Mutation(
    NodeMutations,
    GraphElementMutations,
    PersonMutations,
    ApiKeyMutations,
    DiagramMutations,
    ExecutionMutations,
    UploadMutations,
    UtilityMutations
):
    """Root mutation type combining all mutations."""
    pass