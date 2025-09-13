"""API key mutations using ServiceRegistry."""

import logging

import strawberry

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import API_KEY_SERVICE, LLM_SERVICE
from dipeo.diagram_generated import DomainApiKey
from dipeo.diagram_generated.domain_models import ApiKeyID
from dipeo.diagram_generated.graphql_backups.inputs import CreateApiKeyInput
from dipeo.diagram_generated.graphql_backups.operations import (
    CREATE_API_KEY_MUTATION,
    DELETE_API_KEY_MUTATION,
    TEST_API_KEY_MUTATION,
    CreateApiKeyOperation,
    DeleteApiKeyOperation,
    TestApiKeyOperation,
)
from dipeo.diagram_generated.graphql_backups.results import ApiKeyResult, DeleteResult, TestResult

logger = logging.getLogger(__name__)


# Standalone resolver functions for use with OperationExecutor
async def create_api_key(registry: ServiceRegistry, input: CreateApiKeyInput) -> ApiKeyResult:
    """
    Resolver for CreateApiKey operation.
    Uses the generated CREATE_API_KEY_MUTATION query string.
    """
    try:
        apikey_service = registry.resolve(API_KEY_SERVICE)

        result = await apikey_service.create_api_key(
            label=input.label,
            service=input.service.value,  # Convert enum to string
            key=input.key,
        )

        safe_api_key = DomainApiKey(
            id=result["id"],
            label=result["label"],
            service=input.service,  # Keep as enum
            key="***hidden***",
        )

        return ApiKeyResult.success_result(
            data=safe_api_key, message=f"Created API key: {result['label']}"
        )

    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        return ApiKeyResult.error_result(error=f"Failed to create API key: {e!s}")


async def delete_api_key(registry: ServiceRegistry, api_key_id: strawberry.ID) -> DeleteResult:
    """
    Resolver for DeleteApiKey operation.
    Uses the generated DELETE_API_KEY_MUTATION query string.
    """
    try:
        api_key_id_str = str(api_key_id)
        apikey_service = registry.resolve(API_KEY_SERVICE)

        await apikey_service.delete_api_key(api_key_id_str)

        result = DeleteResult.success_result(
            data=None, message=f"Deleted API key: {api_key_id_str}"
        )
        result.deleted_id = api_key_id_str
        return result

    except Exception as e:
        logger.error(f"Failed to delete API key {api_key_id}: {e}")
        return DeleteResult.error_result(error=f"Failed to delete API key: {e!s}")


async def test_api_key(registry: ServiceRegistry, api_key_id: strawberry.ID) -> TestResult:
    """
    Resolver for TestApiKey operation.
    Uses the generated TEST_API_KEY_MUTATION query string.
    """
    try:
        api_key_id_typed = ApiKeyID(str(api_key_id))
        apikey_service = registry.resolve(API_KEY_SERVICE)
        llm_service = registry.get(LLM_SERVICE)

        if not llm_service:
            return TestResult.error_result(error="LLM service not available")

        api_keys = await apikey_service.list_api_keys()
        api_key = None
        for key in api_keys:
            if key.id == api_key_id_typed:
                api_key = key
                break

        if not api_key:
            return TestResult.error_result(error=f"API key not found: {api_key_id}")

        try:
            models = await llm_service.get_available_models(api_key_id)

            result = TestResult.success_result(
                data=None,
                message=f"API key is valid. Found {len(models)} models: {', '.join(models[:3])}"
                + ("..." if len(models) > 3 else ""),
            )
            result.tested = True
            result.is_valid = True
            return result

        except Exception as test_error:
            logger.warning(f"API key test failed: {test_error}")
            result = TestResult.success_result(
                data=None, message=f"API key test failed: {test_error!s}"
            )
            result.tested = True
            result.is_valid = False
            return result

    except Exception as e:
        logger.error(f"Failed to test API key {api_key_id}: {e}")
        return TestResult.error_result(error=f"Failed to test API key: {e!s}")


def create_api_key_mutations(registry: ServiceRegistry) -> type:
    """Create API key mutation methods with injected registry."""

    @strawberry.type
    class ApiKeyMutations:
        @strawberry.mutation
        async def create_api_key(self, input: CreateApiKeyInput) -> ApiKeyResult:
            """Mutation method that delegates to standalone resolver."""
            return await create_api_key(registry, input)

        @strawberry.mutation
        async def delete_api_key(self, api_key_id: strawberry.ID) -> DeleteResult:
            """Mutation method that delegates to standalone resolver."""
            return await delete_api_key(registry, api_key_id)

        @strawberry.mutation
        async def test_api_key(self, api_key_id: strawberry.ID) -> TestResult:
            """Mutation method that delegates to standalone resolver."""
            return await test_api_key(registry, api_key_id)

    return ApiKeyMutations
