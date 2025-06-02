from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import json
import inspect
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ...services.diagram_service import DiagramService
from ...core.execution.engine import UnifiedExecutionEngine
from ...services.llm_service import LLMService
from ...services.file_service import FileService
from ...services.api_key_service import APIKeyService
from ...utils.dependencies import get_diagram_service, get_llm_service, get_file_service, get_api_key_service
from ...core import handle_api_errors
from ...exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["diagram"])


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

@router.post("/v2/run-diagram")
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
    
    # Check for start nodes
    start_nodes = [node for node in nodes if node.get("type") == "start"]
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
    
    # Create execution engine with services
    execution_engine = UnifiedExecutionEngine(
        llm_service=llm_service,
        file_service=file_service
    )
    
    # Load API keys for LLM calls
    api_keys = await api_key_service.get_all_api_keys()
    
    # Create diagram with API keys context
    enhanced_diagram = {
        **diagram,
        "api_keys": {key["name"]: key["key"] for key in api_keys}
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




@router.get("/v2/execution-capabilities")
@handle_api_errors
async def get_execution_capabilities():
    """Get information about execution capabilities and supported node types"""
    return {
        "version": "2.0",
        "execution_model": "unified_backend",
        "supported_node_types": [
            "start",
            "condition", 
            "job",
            "endpoint",
            "personjob",
            "person_job",
            "personbatchjob", 
            "person_batch_job",
            "db"
        ],
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


@router.get("/v2/health")
@handle_api_errors
async def health_check():
    """Health check endpoint for V2 API"""
    return {
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }


# Legacy Endpoints (for backward compatibility)




@router.post("/import-yaml") 
async def import_yaml(
    payload: dict,
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Import YAML agent definitions and return a diagram state."""
    yaml_text = payload.get('yaml', '')
    return diagram_service.import_yaml(yaml_text)




@router.post("/save")
async def save_diagram(
    payload: dict
):
    """Save diagram to file."""
    from pathlib import Path
    import yaml
    
    diagram = payload.get('diagram', {})
    filename = payload.get('filename', 'diagram.json')
    file_format = payload.get('format', 'json')
    
    try:
        # Initialize file service
        file_service = FileService()
        
        # Ensure filename has correct extension
        file_path = Path(filename)
        if file_format == 'yaml' and not file_path.suffix.lower() in ['.yaml', '.yml']:
            file_path = file_path.with_suffix('.yaml')
        elif file_format == 'json' and file_path.suffix.lower() not in ['.json']:
            file_path = file_path.with_suffix('.json')
        
        # Prepare file path in diagrams directory
        save_path = f"diagrams/{file_path.name}"
        
        # Save based on format
        if file_format == 'yaml':
            # Convert diagram to YAML format
            yaml_content = yaml.dump(diagram, default_flow_style=False, sort_keys=False)
            saved_path = await file_service.write(save_path, yaml_content, relative_to="base", format="text")
        else:
            # Save as JSON
            saved_path = await file_service.write(save_path, diagram, relative_to="base", format="json")
        
        return {
            "success": True,
            "message": f"Diagram saved successfully as {file_format.upper()}",
            "path": saved_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/diagram-stats")
async def get_diagram_stats(
    payload: dict
):
    """Analyze diagram and return statistics."""
    diagram = payload.get('diagram', {})
    
    try:
        # Basic stats calculation
        nodes = diagram.get('nodes', [])
        arrows = diagram.get('arrows', [])
        
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        stats = {
            "node_count": len(nodes),
            "arrow_count": len(arrows),
            "node_types": node_types,
            "persons": len([n for n in nodes if n.get('type') == 'personNode']),
            "jobs": len([n for n in nodes if n.get('type') == 'jobNode']),
            "databases": len([n for n in nodes if n.get('type') == 'dbNode']),
            "conditions": len([n for n in nodes if n.get('type') == 'conditionNode'])
        }
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e)
            }
        )