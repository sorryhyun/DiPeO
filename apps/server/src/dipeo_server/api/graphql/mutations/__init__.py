import strawberry

from .apikey_mutation import ApiKeyMutations
from .arrow_mutation import ArrowMutations
from .diagram_mutation import DiagramMutations
from .execution_mutation import ExecutionMutations
from .handle_mutation import HandleMutations
from .node_mutation import NodeMutations
from .person_mutation import PersonMutations
from .upload_mutation import (
    DiagramConvertResult,
    DiagramValidationResult,
    UploadMutations,
)

__all__ = [
    "ApiKeyMutations",
    "ArrowMutations",
    "DiagramConvertResult",
    "DiagramMutations",
    "DiagramValidationResult",
    "ExecutionMutations",
    "HandleMutations",
    "Mutation",
    "NodeMutations",
    "PersonMutations",
    "UploadMutations",
]


@strawberry.type
class Mutation(
    ApiKeyMutations,
    ArrowMutations,
    DiagramMutations,
    ExecutionMutations,
    HandleMutations,
    NodeMutations,
    PersonMutations,
    UploadMutations,
):
    """Combined GraphQL mutation type."""

    pass
