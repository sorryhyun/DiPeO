import strawberry

# Generated mutations
from ..generated.mutations.apikey_mutation import ApiKeyMutations

# Custom mutations
from ..custom.mutations.custom_mutations import CustomMutations
from ..custom.mutations.execution_mutation import ExecutionMutations
from .upload_mutation import (
    DiagramConvertResult,
    DiagramValidationResult,
    UploadMutations,
)
from .mapped_mutations import MappedMutations

__all__ = [
    "ApiKeyMutations",
    "CustomMutations",
    "DiagramConvertResult",
    "DiagramValidationResult",
    "ExecutionMutations",
    "MappedMutations",
    "Mutation",
    "UploadMutations",
]


@strawberry.type
class Mutation(
    ApiKeyMutations,
    CustomMutations,
    ExecutionMutations,
    MappedMutations,
    UploadMutations,
):
    """Combined GraphQL mutation type."""

    pass
