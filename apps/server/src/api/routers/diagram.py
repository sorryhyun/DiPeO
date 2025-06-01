from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import json
import inspect
import asyncio
import uuid
from typing import Dict, Any

from ...services.diagram_service import DiagramService
from ...utils.dependencies import get_diagram_service

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


async def execution_stream_generator(diagram_data: Dict[str, Any]):
    """Generate SSE stream for diagram execution status updates."""
    execution_id = str(uuid.uuid4())
    
    try:
        # Send execution started event
        yield f"data: {json.dumps({'type': 'execution_started', 'execution_id': execution_id})}\n\n"
        
        # This is a placeholder that provides the streaming interface
        # The actual execution happens in the frontend via the hybrid execution model
        # Frontend executes client-safe nodes locally and calls backend APIs for server-only nodes
        
        nodes = diagram_data.get('nodes', [])
        start_nodes = [n for n in nodes if n.get('type') == 'startNode']
        
        if not start_nodes:
            yield f"data: {json.dumps({'type': 'execution_error', 'error': 'No start nodes found'})}\n\n"
            return
        
        # Simple simulation for SSE interface
        # Real execution happens in frontend with backend API calls for server-only nodes
        for node in nodes:
            node_id = node.get('id')
            node_type = node.get('type', 'unknown')
            
            if not node_id:
                continue
                
            # Start node
            yield f"data: {json.dumps({'type': 'node_start', 'nodeId': node_id})}\n\n"
            
            # Simulate processing
            await asyncio.sleep(0.5)
            
            # Complete node
            yield f"data: {json.dumps({'type': 'node_complete', 'nodeId': node_id})}\n\n"
        
        # Execution complete
        yield f"data: {json.dumps({'type': 'execution_complete', 'execution_id': execution_id, 'context': {'execution_id': execution_id}})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'execution_error', 'error': str(e)})}\n\n"


@router.post("/stream/run-diagram")
async def stream_run_diagram(diagram_data: dict):
    """
    Execute diagram with SSE streaming updates.
    
    This is a placeholder endpoint that provides the streaming interface
    expected by the frontend. The actual execution happens in the frontend
    using the hybrid execution model:
    - Frontend executes client-safe nodes locally
    - Frontend calls backend APIs for server-only nodes (PersonJob, DB, etc.)
    """
    return StreamingResponse(
        execution_stream_generator(diagram_data),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.post("/run-diagram")
async def run_diagram(diagram_data: dict):
    """
    Execute diagram synchronously.
    
    This is a simplified implementation for synchronous execution.
    """
    try:
        nodes = diagram_data.get('nodes', [])
        start_nodes = [n for n in nodes if n.get('type') == 'startNode']
        
        if not start_nodes:
            raise HTTPException(status_code=400, detail="No start nodes found")
        
        execution_id = str(uuid.uuid4())
        
        return {
            "success": True,
            "execution_id": execution_id,
            "context": {
                "execution_id": execution_id,
                "nodes_processed": len(nodes)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-uml")
async def import_uml(
    payload: dict, 
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Import UML text and return a diagram state."""
    uml_text = payload.get('uml', '')
    return diagram_service.import_uml(uml_text)


@router.post("/import-yaml") 
async def import_yaml(
    payload: dict,
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Import YAML agent definitions and return a diagram state."""
    yaml_text = payload.get('yaml', '')
    return diagram_service.import_yaml(yaml_text)


@router.post("/export-uml")
async def export_uml(
    payload: dict,
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Export diagram state to UML text."""
    diagram = payload.get('diagram', {})
    return diagram_service.export_uml(diagram)


@router.post("/save")
async def save_diagram(
    payload: dict
):
    """Save diagram to file."""
    from ...services.unified_file_service import UnifiedFileService
    from pathlib import Path
    import yaml
    
    diagram = payload.get('diagram', {})
    filename = payload.get('filename', 'diagram.json')
    file_format = payload.get('format', 'json')
    
    try:
        # Initialize file service
        file_service = UnifiedFileService()
        
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