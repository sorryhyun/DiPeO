from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import json
import yaml
import inspect
from typing import Dict, Any
import logging
from datetime import datetime

from ...services.file_service import FileService
from ...services.diagram_service import DiagramService
from ...services.llm_service import LLMService
from ...utils.dependencies import get_file_service, get_diagram_service, get_llm_service
from ...engine import handle_api_errors
from ...exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diagrams", tags=["diagram"])


class SafeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles non-serializable objects."""
    
    def default(self, obj):
        if inspect.iscoroutine(obj):
            return f"<coroutine: {obj.__name__ if hasattr(obj, '__name__') else str(obj)}>"
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            return f"<function: {obj.__name__}>"
        elif hasattr(obj, '__dict__'):
            # Try to serialize objects with __dict__
            try:
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            except:
                return f"<object: {type(obj).__name__}>"
        else:
            return f"<non-serializable: {type(obj).__name__}>"


def safe_json_dumps(obj):
    """Safely serialize objects to JSON, handling non-serializable types."""
    return json.dumps(obj, cls=SafeJSONEncoder, default=str)




# V2 Unified Execution Endpoints





@router.get("/execution-capabilities")
@handle_api_errors
async def get_execution_capabilities():
    """Get information about execution capabilities and supported node types"""
    return {
        "version": "2.0",
        "execution_model": "unified_backend",
        "supported_node_types": ["start", "person_job", "person_batch_job", "condition", "db", "job", "endpoint"],
        "features": {
            "streaming_execution": True,
            "parallel_execution": True,
            "loop_control": True,
            "skip_management": True,
            "error_handling": True,
            "cost_tracking": True,
            "variable_substitution": True
        },
        "supported_languages": {
            "job_executor": ["python", "javascript", "bash"]
        },
        "supported_llm_services": ["openai", "claude", "gemini", "grok"]
    }


# Moved from files.py

class SaveDiagramRequest(BaseModel):
    diagram: Dict[str, Any]
    filename: str
    format: str  # "json" or "yaml"


class ConvertDiagramRequest(BaseModel):
    content: str
    from_format: str  # "yaml", "json", "llm-yaml", "uml"
    to_format: str    # "yaml", "json", "llm-yaml", "uml"


class InitializeModelRequest(BaseModel):
    service: str
    model: str
    api_key_id: str


class ImportYamlRequest(BaseModel):
    yaml: str


@router.post("/save")
@handle_api_errors
async def save_diagram(
    request: SaveDiagramRequest,
    file_service: FileService = Depends(get_file_service)
):
    """Save diagram to the appropriate directory based on format."""
    try:
        # Determine file path based on format
        filename = request.filename
        
        # Determine the directory based on format and filename
        if "llm-yaml" in filename or "llm.yaml" in filename:
            directory = "files/llm-yaml_diagrams"
            if not filename.endswith(('.yaml', '.yml')):
                filename += ".yaml"
        elif request.format == "yaml":
            directory = "files/yaml_diagrams"
            if not filename.endswith(('.yaml', '.yml')):
                filename += ".yaml"
        else:
            directory = "files/diagrams"
            if not filename.endswith('.json'):
                filename += ".json"
        
        # Create directory if it doesn't exist
        import os
        dir_path = os.path.join(os.environ.get('BASE_DIR', '.'), directory)
        os.makedirs(dir_path, exist_ok=True)
        
        # Save to appropriate directory
        saved_path = await file_service.write(
            path=f"{directory}/{filename}",
            content=request.diagram,
            format=request.format
        )
        
        return {
            "success": True,
            "message": f"Diagram saved to {saved_path}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert")
@handle_api_errors
async def convert_diagram(
    request: ConvertDiagramRequest,
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Convert diagram between different formats (JSON, YAML, LLM-YAML, UML)."""
    try:
        # Parse input based on format
        if request.from_format == "yaml":
            diagram = yaml.safe_load(request.content)
        elif request.from_format == "json":
            diagram = json.loads(request.content)
        elif request.from_format == "llm-yaml":
            # Use diagram service to import LLM-friendly YAML
            diagram = diagram_service.import_yaml(request.content)
        else:
            raise ValidationError(f"Unsupported from_format: {request.from_format}")
        
        # Convert to target format
        if request.to_format == "yaml":
            output = yaml.dump(
                diagram,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2
            )
        elif request.to_format == "json":
            output = json.dumps(diagram, indent=2)
        elif request.to_format == "llm-yaml":
            # Convert to LLM-friendly YAML format
            output = diagram_service.export_llm_yaml(diagram)
        else:
            raise ValidationError(f"Unsupported to_format: {request.to_format}")
        
        return {
            "success": True,
            "output": output,
            "message": f"Converted from {request.from_format} to {request.to_format}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
@handle_api_errors
async def health_check():
    """Health check endpoint for V2 API"""
    return {
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/../initialize-model")
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


@router.post("/../import-yaml")
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


