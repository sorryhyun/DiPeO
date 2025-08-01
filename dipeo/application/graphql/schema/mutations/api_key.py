"""API key mutations using ServiceRegistry."""

import logging

import strawberry

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import API_KEY_SERVICE, LLM_SERVICE
from dipeo.core.ports import APIKeyPort
from dipeo.diagram_generated import DomainApiKey
from dipeo.diagram_generated.domain_models import ApiKeyID

from ...types.inputs import CreateApiKeyInput
from ...types.results import ApiKeyResult, DeleteResult, TestApiKeyResult

logger = logging.getLogger(__name__)


def create_api_key_mutations(registry: ServiceRegistry) -> type:
    """Create API key mutation methods with injected service registry."""
    
    @strawberry.type
    class ApiKeyMutations:
        @strawberry.mutation
        async def create_api_key(self, input: CreateApiKeyInput) -> ApiKeyResult:
            try:
                apikey_service = registry.resolve(API_KEY_SERVICE)
                
                # Create API key using the service
                result = await apikey_service.create_api_key(
                    label=input.label,
                    service=input.service.value,  # Convert enum to string
                    key=input.key
                )
                
                # Return without exposing the actual key
                safe_api_key = DomainApiKey(
                    id=result["id"],
                    label=result["label"],
                    service=input.service,  # Keep as enum
                    key="***hidden***",
                )
                
                return ApiKeyResult(
                    success=True,
                    api_key=safe_api_key,
                    message=f"Created API key: {result['label']}",
                )
                
            except Exception as e:
                logger.error(f"Failed to create API key: {e}")
                return ApiKeyResult(
                    success=False,
                    error=f"Failed to create API key: {str(e)}",
                )
        
        @strawberry.mutation
        async def delete_api_key(self, id: strawberry.ID) -> DeleteResult:
            try:
                api_key_id = str(id)
                apikey_service = registry.resolve(API_KEY_SERVICE)
                
                # Delete API key
                await apikey_service.delete_api_key(api_key_id)
                
                return DeleteResult(
                    success=True,
                    deleted_id=api_key_id,
                    message=f"Deleted API key: {api_key_id}",
                )
                
            except Exception as e:
                logger.error(f"Failed to delete API key {api_key_id}: {e}")
                return DeleteResult(
                    success=False,
                    error=f"Failed to delete API key: {str(e)}",
                )
        
        @strawberry.mutation
        async def test_api_key(self, id: strawberry.ID) -> TestApiKeyResult:
            try:
                api_key_id = ApiKeyID(str(id))
                apikey_service = registry.resolve(API_KEY_SERVICE)
                llm_service = registry.get(LLM_SERVICE.name)
                
                if not llm_service:
                    return TestApiKeyResult(
                        success=False,
                        error="LLM service not available",
                    )
                
                # Get API key
                api_keys = await apikey_service.list_api_keys()
                api_key = None
                for key in api_keys:
                    if key.id == api_key_id:
                        api_key = key
                        break
                
                if not api_key:
                    return TestApiKeyResult(
                        success=False,
                        error=f"API key not found: {api_key_id}",
                    )
                
                # Test the API key
                try:
                    models = await llm_service.get_available_models(
                        api_key_id
                    )
                    
                    return TestApiKeyResult(
                        success=True,
                        message=f"API key is valid for {api_key.service}",
                        model_info={
                            "service": api_key.service,
                            "available_models": models,
                            "model_count": len(models),
                        }
                    )
                except Exception as test_error:
                    return TestApiKeyResult(
                        success=False,
                        error=f"API key test failed: {str(test_error)}",
                    )
                
            except Exception as e:
                logger.error(f"Failed to test API key {id}: {e}")
                return TestApiKeyResult(
                    success=False,
                    error=f"Failed to test API key: {str(e)}",
                )
    
    return ApiKeyMutations