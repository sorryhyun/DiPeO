from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...services.api_key_service import APIKeyService
from ...services.llm_service import LLMService
from ...utils.dependencies import get_api_key_service, get_llm_service
from ...llm_adapters import SUPPORTED_MODELS

router = APIRouter(prefix="/api", tags=["apikeys"])


@router.get("/models")
async def get_models():
    """Get list of supported LLM models."""
    return {
        "models": list(SUPPORTED_MODELS.keys()),
        "providers": {
            "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "Anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            "Google": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
            "xAI": ["grok-2-latest", "grok-2-vision-1212"]
        }
    }


@router.get("/apikeys")
async def get_api_keys(
    api_key_service: APIKeyService = Depends(get_api_key_service)
) -> List[dict]:
    """Get all stored API keys (masked)."""
    return api_key_service.get_all_keys()


@router.post("/apikeys")
async def add_api_key(
    payload: dict,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Add a new API key."""
    provider = payload.get('provider')
    key = payload.get('key')
    
    if not provider or not key:
        raise HTTPException(status_code=400, detail="Provider and key are required")
    
    api_key_service.add_key(provider, key)
    return {"message": "API key added successfully"}


@router.delete("/apikeys/{key_id}")
async def delete_api_key(
    key_id: str,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Delete an API key."""
    api_key_service.delete_api_key(key_id)
    return {"message": "API key deleted successfully"}


@router.post("/llm")
async def test_llm(
    payload: dict,
    llm_service: LLMService = Depends(get_llm_service)
):
    """Test LLM endpoint with a simple query."""
    model = payload.get('model', 'gpt-3.5-turbo')
    messages = payload.get('messages', [{"role": "user", "content": "Say 'Hello, World!'"}])
    
    try:
        response = await llm_service.chat(messages, model=model)
        return {
            "success": True,
            "response": response.content,
            "model": response.model,
            "usage": response.usage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))