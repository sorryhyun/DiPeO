"""Mapped mutations to match frontend expectations with snake_case naming."""

import strawberry
from typing import Optional

from ..context import GraphQLContext
from ..generated.types import (
    CreateApiKeyInput,
    UpdateApiKeyInput,
    ApiKeyResult,
    ApiKeyID,
    DeleteResult,
)
from ..generated.mutations.apikey_mutation import ApiKeyMutations
# Note: Node, Person, Handle, Arrow mutations are managed through diagram operations
# and are not exposed as individual mutations


@strawberry.type
class MappedMutations:
    """Provides snake_case aliases for auto-generated mutations."""
    
    # API Key mutations with snake_case
    @strawberry.mutation
    async def create_api_key(
        self,
        input: CreateApiKeyInput,
        info: strawberry.Info[GraphQLContext],
    ) -> ApiKeyResult:
        """Create a new API key (snake_case alias)."""
        mutations = ApiKeyMutations()
        return await mutations.create_apikey(input, info)
    
    @strawberry.mutation
    async def update_api_key(
        self,
        input: UpdateApiKeyInput,
        info: strawberry.Info[GraphQLContext],
    ) -> ApiKeyResult:
        """Update an API key (snake_case alias)."""
        mutations = ApiKeyMutations()
        return await mutations.update_apikey(input, info)
    
    @strawberry.mutation
    async def delete_api_key(
        self,
        id: ApiKeyID,
        info: strawberry.Info[GraphQLContext],
    ) -> DeleteResult:
        """Delete an API key (snake_case alias)."""
        mutations = ApiKeyMutations()
        return await mutations.delete_apikey(id, info)
    
    # Note: Node, Person, Handle, Arrow mutations are managed through diagram operations
    # These entities are diagram-scoped and should be created/updated/deleted
    # through the diagram mutations in custom_mutations.py