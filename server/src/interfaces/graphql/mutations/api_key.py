"""Refactored API Key related GraphQL mutations using Pydantic models."""
import strawberry
import logging

from ..types.results import ApiKeyResult, DeleteResult, TestApiKeyResult
from ..types.scalars import ApiKeyID
from ..types.inputs import CreateApiKeyInput
from ..context import GraphQLContext
from src.domains.diagram.models.domain import DomainApiKey
from ..models.input_models import CreateApiKeyInput as PydanticCreateApiKeyInput

logger = logging.getLogger(__name__)


@strawberry.type
class ApiKeyMutations:
    """Mutations for API key operations."""
    
    @strawberry.mutation
    async def create_api_key(self, input: CreateApiKeyInput, info) -> ApiKeyResult:
        """Create a new API key."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticCreateApiKeyInput(
                label=input.label,
                service=input.service,
                key=input.key
            )
            
            # Create API key using validated data
            api_key_data = api_key_service.create_api_key(
                label=pydantic_input.label,  # Already trimmed by validation
                service=pydantic_input.service.value,
                key=pydantic_input.key  # Already masked in validation
            )
            
            # Create Pydantic model
            api_key = DomainApiKey(
                id=api_key_data['id'],
                label=api_key_data['label'],
                service=pydantic_input.service
            )
            
            return ApiKeyResult(
                success=True,
                api_key=api_key,  # Strawberry will handle conversion
                message=f"Created API key {api_key.id}"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error creating API key: {e}")
            return ApiKeyResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            return ApiKeyResult(
                success=False,
                error=f"Failed to create API key: {str(e)}"
            )
    
    @strawberry.mutation
    async def test_api_key(self, id: ApiKeyID, info) -> TestApiKeyResult:
        """Test an API key to verify it works."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            llm_service = context.llm_service
            
            # Get API key
            api_key_data = api_key_service.get_api_key(id)
            if not api_key_data:
                return TestApiKeyResult(
                    success=False,
                    valid=False,
                    error="API key not found"
                )
            
            # Test the API key by getting available models
            try:
                models = llm_service.get_available_models(
                    service=api_key_data['service'],
                    api_key_id=id
                )
                
                return TestApiKeyResult(
                    success=True,
                    valid=True,
                    available_models=models,
                    message=f"API key is valid. {len(models)} models available."
                )
                
            except Exception as test_error:
                return TestApiKeyResult(
                    success=True,
                    valid=False,
                    error=f"API key test failed: {str(test_error)}"
                )
                
        except Exception as e:
            logger.error(f"Failed to test API key {id}: {e}")
            return TestApiKeyResult(
                success=False,
                valid=False,
                error=f"Failed to test API key: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_api_key(self, id: ApiKeyID, info) -> DeleteResult:
        """Delete an API key."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.api_key_service
            
            # Check if API key exists
            api_key_data = api_key_service.get_api_key(id)
            if not api_key_data:
                return DeleteResult(
                    success=False,
                    error=f"API key {id} not found"
                )
            
            # Delete API key
            api_key_service.delete_api_key(id)
            
            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted API key {id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete API key {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete API key: {str(e)}"
            )