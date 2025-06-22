"""GraphQL mutations for API key management."""

import logging

import strawberry

from dipeo_domain import DomainApiKey

from ..context import GraphQLContext
from ..graphql_types import (
    ApiKeyID,
    ApiKeyResult,
    CreateApiKeyInput,
    DeleteResult,
    DomainApiKeyType,
    TestApiKeyResult,
)

logger = logging.getLogger(__name__)


@strawberry.type
class ApiKeyMutations:
    """Handles API key CRUD operations."""

    @strawberry.mutation
    async def create_api_key(self, input: CreateApiKeyInput, info) -> ApiKeyResult:
        """Creates new API key."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service

            api_key_data = api_key_service.create_api_key(
                label=input.label,
                service=input.service.value,
                key=input.key,
            )

            api_key = DomainApiKey(
                id=api_key_data["id"],
                label=api_key_data["label"],
                service=input.service,
                masked_key=f"{input.service.value}-****",
            )

            return ApiKeyResult(
                success=True, api_key=api_key, message=f"Created API key {api_key.id}"
            )

        except ValueError as e:
            logger.error(f"Validation error creating API key: {e}")
            return ApiKeyResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            return ApiKeyResult(
                success=False, error=f"Failed to create API key: {e!s}"
            )

    @strawberry.mutation
    async def test_api_key(self, id: ApiKeyID, info) -> TestApiKeyResult:
        """Tests API key validity."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            llm_service = context.llm_service

            api_key_data = api_key_service.get_api_key(id)
            if not api_key_data:
                return TestApiKeyResult(
                    success=False, valid=False, error="API key not found"
                )

            try:
                models = llm_service.get_available_models(
                    service=api_key_data["service"], api_key_id=id
                )

                return TestApiKeyResult(
                    success=True,
                    valid=True,
                    available_models=models,
                    message=f"API key is valid. {len(models)} models available.",
                )

            except Exception as test_error:
                return TestApiKeyResult(
                    success=True,
                    valid=False,
                    error=f"API key test failed: {test_error!s}",
                )

        except Exception as e:
            logger.error(f"Failed to test API key {id}: {e}")
            return TestApiKeyResult(
                success=False, valid=False, error=f"Failed to test API key: {e!s}"
            )

    @strawberry.mutation
    async def delete_api_key(self, id: ApiKeyID, info) -> DeleteResult:
        """Removes API key."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service

            api_key_data = api_key_service.get_api_key(id)
            if not api_key_data:
                return DeleteResult(success=False, error=f"API key {id} not found")

            api_key_service.delete_api_key(id)

            return DeleteResult(
                success=True, deleted_id=id, message=f"Deleted API key {id}"
            )

        except Exception as e:
            logger.error(f"Failed to delete API key {id}: {e}")
            return DeleteResult(
                success=False, error=f"Failed to delete API key: {e!s}"
            )
