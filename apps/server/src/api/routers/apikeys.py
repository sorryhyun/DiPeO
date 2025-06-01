from fastapi import APIRouter, Depends
from typing import List

from ...services.api_key_service import APIKeyService
from ...services.llm_service import LLMService
from ...utils.dependencies import get_api_key_service, get_llm_service
from ...core import handle_api_errors
from ...exceptions import ValidationError

router = APIRouter(prefix="/api", tags=["apikeys"])


@router.get("/models")
async def get_models(
    service: str = None,
    api_key_id: str = None,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Get list of supported LLM models."""
    # If no service or API key specified, return empty models
    if not service or not api_key_id:
        return {
            "models": [],
            "providers": {
                "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "Anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
                "Google": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
                "xAI": ["grok-2-latest", "grok-2-vision-1212"]
            }
        }
    
    # Verify API key exists and matches service
    try:
        api_key = api_key_service.get_api_key(api_key_id)
        if not api_key or api_key.get('service') != service:
            return {"models": [], "error": "Invalid API key or service mismatch"}
    except (KeyError, FileNotFoundError, ValueError) as e:
        return {"models": [], "error": "API key not found"}
    
    # Get actual API key value to make real API calls
    api_key_value = api_key.get('key')
    if not api_key_value:
        return {"models": [], "error": "API key value not found"}
    
    # Use factory to create adapter and fetch models
    try:
        from ...llm.factory import create_adapter
        adapter = create_adapter(service, "dummy-model", api_key_value)
        models = adapter.list_models()
        return {"models": models}
    except Exception as e:
        # Return fallback models if adapter creation or API call fails
        service_models = {
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "claude": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            "gemini": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
            "grok": ["grok-2-latest", "grok-2-vision-1212"]
        }
        models = service_models.get(service, [])
        return {"models": models}


@router.get("/keys")
async def get_api_keys(
    api_key_service: APIKeyService = Depends(get_api_key_service)
) -> List[dict]:
    """Get all stored API keys (masked)."""
    return api_key_service.list_api_keys()


@router.post("/keys")
@handle_api_errors
async def add_api_key(
    payload: dict,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Add a new API key."""
    # Support both 'provider' and 'service' field names for compatibility
    service = payload.get('service') or payload.get('provider')
    key = payload.get('key')
    name = payload.get('name')
    
    if not service or not key:
        raise ValidationError("Service/provider and key are required")
    
    # Use provided name or generate default
    if not name:
        name = f"{service} API Key"
    
    # Create the API key and return the result
    created_key = api_key_service.create_api_key(name, service, key)
    return created_key


@router.delete("/keys/{key_id}")
@handle_api_errors
async def delete_api_key(
    key_id: str,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Delete an API key."""
    api_key_service.delete_api_key(key_id)
    return {"message": "API key deleted successfully"}


@router.post("/initialize-model")
@handle_api_errors
async def initialize_model(
    payload: dict,
    llm_service: LLMService = Depends(get_llm_service)
):
    """Pre-initialize a model client for faster subsequent use."""
    service = payload.get('service')
    model = payload.get('model') 
    api_key_id = payload.get('api_key_id')
    
    if not service or not model or not api_key_id:
        raise ValidationError("Service, model, and api_key_id are required")
    
    try:
        llm_service.pre_initialize_model(service, model, api_key_id)
        return {
            "success": True,
            "message": f"Model {model} for service {service} has been pre-initialized"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/llm")
@handle_api_errors
async def test_llm(
    payload: dict,
    llm_service: LLMService = Depends(get_llm_service)
):
    """Test LLM endpoint with a simple query."""
    service = payload.get('service', 'openai')
    api_key_id = payload.get('api_key_id')
    model = payload.get('model', 'gpt-3.5-turbo')
    messages = payload.get('messages', "Say 'Hello, World!'")
    
    if not api_key_id:
        raise ValidationError("api_key_id is required")
    
    response = await llm_service.call_llm(service, api_key_id, model, messages)
    return {
        "success": True,
        "response": response["response"],
        "cost": response["cost"]
    }