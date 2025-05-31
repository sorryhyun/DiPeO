from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import json
import inspect

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
    """Save diagram to file - placeholder endpoint."""
    # This endpoint would typically integrate with a file service
    # For now, return a success response
    diagram = payload.get('diagram', {})
    filename = payload.get('filename', 'diagram.json')
    file_format = payload.get('format', 'json')
    
    try:
        
        # TODO: Implement actual file saving logic
        # This would typically use UnifiedFileService
        
        return {
            "success": True,
            "message": f"Diagram save endpoint called for {filename} as {file_format.upper()}"
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