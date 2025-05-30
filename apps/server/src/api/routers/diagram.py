from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import AsyncGenerator
import json
import asyncio
import inspect

from ...services.diagram_service import DiagramService
from ...services.memory_service import MemoryService
from ...utils.dependencies import get_diagram_service, get_memory_service
from ...streaming import StreamingDiagramExecutor
from ...run_graph import DiagramExecutor

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


@router.post("/stream/run-diagram")
@router.post("/run-diagram")
async def run_diagram_endpoint(payload: dict):
    """
    Execute a diagram with streaming node status updates.
    Returns a streaming response with real-time node execution status.
    """
    diagram = payload.get('diagram', payload)  # Handle both formats
    broadcast = payload.get('broadcast', True)  # Keep for API compatibility (SSE always broadcasts)
    memory_service = get_memory_service()
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming updates during diagram execution."""
        # Create streaming executor
        executor = StreamingDiagramExecutor(
            diagram=diagram,
            memory_service=memory_service
        )
        
        # Start execution
        execution_task = asyncio.create_task(executor.execute())
        
        try:
            # Send initial connection confirmation
            yield f"data: {safe_json_dumps({'type': 'connection_established'})}\n\n"
            
            # Give the execution task time to initialize the stream
            await asyncio.sleep(0.1)
            
            # Wait for stream to be ready
            if not await executor.wait_for_stream_ready():
                raise HTTPException(status_code=500, detail="Failed to initialize stream")
            
            # Get the SSE queue
            queue = executor.get_stream_queue()
            
            # Stream updates until completion
            while not executor.completed or (queue and not queue.empty()):
                if queue:
                    try:
                        update = await asyncio.wait_for(queue.get(), timeout=0.1)
                        yield f"data: {safe_json_dumps(update)}\n\n"
                    except asyncio.TimeoutError:
                        # Send heartbeat to keep connection alive
                        yield f": heartbeat\n\n"
                        continue
                else:
                    await asyncio.sleep(0.1)
            
            # Wait for execution to complete
            await execution_task
            
            # Check for errors
            if executor.error:
                raise executor.error
                
        except Exception as e:
            if not execution_task.done():
                execution_task.cancel()
            raise HTTPException(status_code=500, detail=str(e))
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked"
        }
    )


@router.post("/external/run-diagram")
async def external_run_diagram(payload: dict):
    """Alias for run-diagram endpoint for external access."""
    return await run_diagram_endpoint(payload)


@router.post("/run-diagram-sync")
async def run_diagram_sync(
    payload: dict,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Execute diagram synchronously and return complete results."""
    diagram = payload.get('diagram', {})
    
    executor = DiagramExecutor(diagram=diagram, memory_service=memory_service)
    context, total_cost = await executor.run()
    
    return {
        "success": True,
        "context": context,
        "total_cost": total_cost,
        "execution_id": executor.execution_id
    }


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