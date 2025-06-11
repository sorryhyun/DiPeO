from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging

from ...services.llm_service import LLMService
from ...services.diagram_service import DiagramService
from ...utils.dependencies import get_llm_service, get_diagram_service
from ...engine import handle_api_errors

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["models"])


class InitializeModelRequest(BaseModel):
    service: str
    model: str
    api_key_id: str


class ImportYamlRequest(BaseModel):
    yaml: str


@router.post("/initialize-model")
@handle_api_errors
async def initialize_model(
    request: InitializeModelRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """Pre-initialize/warm up a model for faster first execution."""
    try:
        # Use LLM service to create adapter and warm it up
        from ...llm.factory import create_adapter
        from ...services.api_key_service import APIKeyService
        
        # Get API key
        api_key_service = APIKeyService()
        api_key = api_key_service.get_api_key(request.api_key_id)
        
        # Create adapter to warm up the model
        adapter = create_adapter(request.service, request.model, api_key['key'])
        
        # Optionally make a minimal call to warm up the connection
        # This helps with cold starts for some providers
        logger.info(f"Initializing model {request.service}:{request.model}")
        
        return {
            "success": True,
            "message": f"Model {request.model} initialized successfully",
            "service": request.service,
            "model": request.model
        }
    except Exception as e:
        logger.error(f"Failed to initialize model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-yaml")
@handle_api_errors
async def import_yaml(
    request: ImportYamlRequest,
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Import a YAML diagram (LLM-friendly format)."""
    try:
        # Import the YAML using diagram service
        diagram = diagram_service.import_yaml(request.yaml)
        
        return {
            "success": True,
            "diagram": diagram,
            "message": "YAML imported successfully"
        }
    except Exception as e:
        logger.error(f"Failed to import YAML: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))