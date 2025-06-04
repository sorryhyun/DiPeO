from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
import logging

from ...services.api_key_service import APIKeyService
from ...services.llm_service import LLMService
from ...utils.dependencies import get_api_key_service, get_llm_service
from ...engine import handle_api_errors
from ...exceptions import ValidationError, APIKeyNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])


class CreateAPIKeyRequest(BaseModel):
    name: str
    service: str  # "openai", "claude", "gemini", "grok"
    key: str


class TestAPIKeyRequest(BaseModel):
    model: str
    messages: str = "Say 'Hello, World!'"


@router.get("/")
async def list_api_keys(
    api_key_service: APIKeyService = Depends(get_api_key_service)
) -> List[dict]:
    """Get all stored API keys (masked)."""
    return api_key_service.list_api_keys()


@router.post("/")
@handle_api_errors
async def create_api_key(
    request: CreateAPIKeyRequest,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Create a new API key."""
    created_key = api_key_service.create_api_key(
        name=request.name,
        service=request.service,
        key=request.key
    )
    return created_key


@router.delete("/{id}")
@handle_api_errors
async def delete_api_key(
    id: str,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Delete an API key."""
    api_key_service.delete_api_key(id)
    return {"message": "API key deleted successfully"}


@router.get("/{id}/models")
@handle_api_errors
async def get_models_for_key(
    id: str,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Get available models for a specific API key."""
    logger.info(f"[Models API] Request for API key: {id}")
    
    # Get API key details
    try:
        api_key = api_key_service.get_api_key(id)
        service = api_key.get('service')
        api_key_value = api_key.get('key')
        
        if not service or not api_key_value:
            raise ValidationError("Invalid API key data")
            
    except (KeyError, FileNotFoundError, ValueError) as e:
        logger.warning(f"[Models API] API key not found: {str(e)}")
        raise APIKeyNotFoundError(f"API key '{id}' not found")
    
    # Try to fetch models from provider
    try:
        from ...llm.factory import create_adapter
        logger.info(f"[Models API] Creating adapter for service: {service}")
        adapter = create_adapter(service, "dummy-model", api_key_value)
        models = adapter.list_models()
        logger.info(f"[Models API] Successfully fetched {len(models)} models")
        return {
            "service": service,
            "models": models
        }
    except Exception as e:
        logger.warning(f"[Models API] Failed to fetch models, using fallback. Error: {str(e)}")
        # Return fallback models if API call fails
        service_models = {
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "claude": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            "gemini": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
            "grok": ["grok-2-latest", "grok-2-vision-1212"]
        }
        return {
            "service": service,
            "models": service_models.get(service, [])
        }


@router.post("/{id}/test")
@handle_api_errors
async def test_api_key(
    id: str,
    request: TestAPIKeyRequest,
    api_key_service: APIKeyService = Depends(get_api_key_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Test an API key with a simple LLM call."""
    # Get API key details
    try:
        api_key = api_key_service.get_api_key(id)
        service = api_key.get('service')
        
        if not service:
            raise ValidationError("Invalid API key data")
            
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise APIKeyNotFoundError(f"API key '{id}' not found")
    
    # Test the API key with LLM call
    try:
        response = await llm_service.call_llm(
            service=service,
            api_key_id=id,
            model=request.model,
            messages=request.messages
        )
        return {
            "success": True,
            "service": service,
            "model": request.model,
            "response": response["response"],
            "cost": response["cost"]
        }
    except Exception as e:
        logger.error(f"[Test API] Failed to test API key: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# Keep this endpoint for backward compatibility during migration
@router.get("/providers")
async def get_supported_providers():
    """Get list of supported LLM providers and their models."""
    return {
        "providers": {
            "OpenAI": {
                "service": "openai",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
            },
            "Anthropic": {
                "service": "claude",
                "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
            },
            "Google": {
                "service": "gemini", 
                "models": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
            },
            "xAI": {
                "service": "grok",
                "models": ["grok-2-latest", "grok-2-vision-1212"]
            }
        }
    }