from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import yaml
import inspect
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from apps.server.src.engine.engine import UnifiedExecutionEngine
from ...services.llm_service import LLMService
from ...services.file_service import FileService
from ...services.api_key_service import APIKeyService
from ...services.diagram_service import DiagramService
from ...utils.dependencies import get_llm_service, get_file_service, get_api_key_service, get_diagram_service
from ...engine import handle_api_errors
from ...exceptions import ValidationError
# node_type_utils no longer needed - all types are already snake_case

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

@router.post("/execute")
@handle_api_errors
async def run_diagram_v2(
    diagram: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None,
    llm_service: LLMService = Depends(get_llm_service),
    file_service: FileService = Depends(get_file_service),
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Execute diagram using unified backend execution engine with SSE streaming.
    
    This V2 endpoint consolidates all node execution on the backend,
    replacing the hybrid client-server model.
    """
    
    # Validate diagram structure
    if not isinstance(diagram, dict):
        raise ValidationError("Diagram must be a dictionary")
    
    nodes = diagram.get("nodes", [])
    arrows = diagram.get("arrows", [])
    
    if not nodes:
        raise ValidationError("Diagram must contain at least one node")
    
    # Check for start nodes using normalized type checking
    # Check both top-level type (React Flow) and data.type (logical type)
    start_nodes = [
        node for node in nodes 
        if node.get("type", "") == "start" or 
           node.get("data", {}).get("type", "") == "start"
    ]
    if not start_nodes:
        raise ValidationError("Diagram must contain at least one start node")
    
    # Set default options
    options = options or {}
    execution_options = {
        "continue_on_error": options.get("continueOnError", False),
        "allow_partial": options.get("allowPartial", False),
        "debug_mode": options.get("debugMode", False),
        **options
    }
    
    # Pre-initialize LLM models before execution
    pre_initialized = set()
    persons = diagram.get("persons", [])
    
    # Extract unique LLM configurations from person definitions
    for person in persons:
        model = person.get("model", "")
        service = person.get("service", "")
        api_key_id = person.get("apiKeyId", "")
        
        if model and service and api_key_id:
            # Create unique key for this configuration
            config_key = f"{service}:{model}:{api_key_id}"
            if config_key not in pre_initialized:
                logger.info(f"Pre-initializing LLM: {service} {model}")
                try:
                    # Pre-initialize the model
                    llm_service.pre_initialize_model(
                        service=service,
                        model=model,
                        api_key_id=api_key_id
                    )
                    pre_initialized.add(config_key)
                except Exception as e:
                    logger.warning(f"Failed to pre-initialize {config_key}: {e}")
                    # Continue even if pre-initialization fails
    
    # Also check PersonJob and PersonBatchJob nodes for embedded person configs
    for node in nodes:
        node_type = node.get("type", "").lower().replace("node", "")
        if node_type in ["personjob", "personbatchjob", "person_job", "person_batch_job"]:
            person_config = node.get("data", {}).get("person", {})
            if person_config:
                model = person_config.get("model", "")
                service = person_config.get("service", "")
                api_key_id = person_config.get("apiKeyId", "")
                
                if model and service and api_key_id:
                    config_key = f"{service}:{model}:{api_key_id}"
                    if config_key not in pre_initialized:
                        logger.info(f"Pre-initializing LLM from node: {service} {model}")
                        try:
                            llm_service.pre_initialize_model(
                                service=service,
                                model=model,
                                api_key_id=api_key_id
                            )
                            pre_initialized.add(config_key)
                        except Exception as e:
                            logger.warning(f"Failed to pre-initialize {config_key}: {e}")
    
    if pre_initialized:
        logger.info(f"Pre-initialized {len(pre_initialized)} unique LLM configurations")
    
    # Create execution engine with services
    execution_engine = UnifiedExecutionEngine(
        llm_service=llm_service,
        file_service=file_service
    )
    
    # Load API keys for LLM calls
    api_keys_list = api_key_service.list_api_keys()
    
    # Get actual key values for each API key
    api_keys_dict = {}
    for key_info in api_keys_list:
        full_key_data = api_key_service.get_api_key(key_info["id"])
        api_keys_dict[key_info["id"]] = full_key_data["key"]
    
    # Create diagram with API keys context
    enhanced_diagram = {
        **diagram,
        "api_keys": api_keys_dict
    }
    
    # Stream execution updates
    async def stream_execution():
        try:
            execution_id = f"exec_{int(datetime.now().timestamp() * 1000)}"
            
            # Send initial response
            yield f"data: {json.dumps({'type': 'execution_started', 'execution_id': execution_id})}\n\n"
            
            # Execute diagram and stream updates
            async for update in execution_engine.execute_diagram(enhanced_diagram, execution_options):
                # Add execution ID to all updates
                update["execution_id"] = execution_id
                
                # Format for SSE
                yield f"data: {json.dumps(update)}\n\n"
            
        except Exception as e:
            error_update = {
                "type": "execution_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_update)}\n\n"
            logger.error(f"Diagram execution failed: {e}", exc_info=True)
    
    return StreamingResponse(
        stream_execution(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )




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


@router.post("/save")
@handle_api_errors
async def save_diagram(
    request: SaveDiagramRequest,
    file_service: FileService = Depends(get_file_service)
):
    """Save diagram to the diagrams directory."""
    try:
        # Determine file path in diagrams directory
        filename = request.filename
        if not filename.endswith(('.json', '.yaml', '.yml')):
            if request.format == "yaml":
                filename += ".yaml"
            else:
                filename += ".json"
        
        # Save to diagrams directory (which is now under files/)
        saved_path = await file_service.write(
            path=f"files/diagrams/{filename}",
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




