import strawberry

from .api_key_mutation import ApiKeyMutations
from .diagram_mutation import DiagramMutations
from .execution_mutation import ExecutionMutations
from .node_mutation import NodeMutations
from .person_mutation import PersonMutations
from .upload_mutation import (
    DiagramConvertResult,
    DiagramValidationResult,
    UploadMutations,
)

__all__ = [
    "ApiKeyMutations",
    "DiagramConvertResult",
    "DiagramMutations",
    "DiagramValidationResult",
    "ExecutionMutations",
    "Mutation",
    "NodeMutations",
    "PersonMutations",
    "UploadMutations",
]


@strawberry.type
class Mutation(
    ApiKeyMutations,
    DiagramMutations,
    ExecutionMutations,
    NodeMutations,
    PersonMutations,
    UploadMutations,
):
    """Combined GraphQL mutation type."""

    pass
