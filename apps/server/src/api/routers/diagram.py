from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import AsyncGenerator
import json
import asyncio
import traceback
import inspect
from datetime import datetime

from ...services.diagram_service import DiagramService
from ...services.memory_service import MemoryService
from ...utils.dependencies import get_diagram_service, get_memory_service
from ...utils.converter import DiagramMigrator
from ...streaming.stream_manager import stream_manager
from ...run_graph import DiagramExecutor
from config import CONVERSATION_LOG_DIR

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


class StreamingExecutor:
    """Executes diagram with streaming updates."""
    
    def __init__(self, broadcast_to_websocket: bool = False):
        self.completed = False
        self.error = None
        self.broadcast_to_websocket = broadcast_to_websocket
        self.execution_id = None
        self.stream_context = None

    async def status_callback(self, update: dict):
        # Publish to stream manager
        if self.execution_id:
            await stream_manager.publish_update(self.execution_id, update)

    async def execute_diagram(self, diagram: dict):
        """Execute diagram and collect all updates."""
        try:
            diagram = DiagramMigrator.migrate(diagram)
            
            memory_service = get_memory_service()
            executor = DiagramExecutor(
                diagram=diagram,
                memory_service=memory_service,
                status_callback=self.status_callback
            )
            self.execution_id = executor.execution_id
            
            # Create stream context
            output_format = 'both' if self.broadcast_to_websocket else 'sse'
            self.stream_context = await stream_manager.create_stream(
                self.execution_id, output_format
            )
            
            # Broadcast execution start
            if self.broadcast_to_websocket:
                await stream_manager.publish_update(self.execution_id, {
                    "type": "execution_started",
                    "execution_id": self.execution_id,
                    "diagram": diagram,
                    "timestamp": datetime.now().isoformat()
                })

            context, total_cost = await executor.run()
            
            log_path = await memory_service.save_conversation_log(
                execution_id=executor.execution_id,
                log_dir=CONVERSATION_LOG_DIR
            )

            await stream_manager.publish_update(self.execution_id, {
                "type": "execution_complete",
                "context": context,
                "total_cost": total_cost,
                "memory_stats": executor.get_memory_stats(),
                "conversation_log": log_path
            })
            
            memory_service.clear_execution_memory(executor.execution_id)

            self.completed = True

        except Exception as e:
            self.error = e
            await stream_manager.publish_update(self.execution_id, {
                "type": "execution_error",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            self.completed = True
        finally:
            # Clean up stream resources
            if self.execution_id:
                await stream_manager.cleanup_stream(self.execution_id)


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
        # Migrate if needed
        migrator = DiagramMigrator()
        migrated_diagram = migrator.migrate(diagram)
        
        # TODO: Implement actual file saving logic
        # This would typically use UnifiedFileService
        
        return {
            "success": True,
            "message": f"Diagram save endpoint called for {filename} as {file_format.upper()}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-diagram")
async def run_diagram_endpoint(diagram: dict, broadcast: bool = True):
    """
    Execute a diagram with streaming node status updates.
    Returns a streaming response with real-time node execution status.
    """
    diagram = DiagramMigrator.migrate(diagram)
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming updates during diagram execution."""

        streaming_executor = StreamingExecutor(broadcast_to_websocket=broadcast)

        execution_task = asyncio.create_task(
            streaming_executor.execute_diagram(diagram)
        )

        try:
            # Send initial connection confirmation
            yield f"data: {safe_json_dumps({'type': 'connection_established'})}\n\n"
            
            # Get the SSE queue from stream manager
            queue = None
            while queue is None and streaming_executor.execution_id:
                queue = stream_manager.get_stream_queue(streaming_executor.execution_id)
                if queue is None:
                    await asyncio.sleep(0.01)  # Wait for stream to be created
            
            while not streaming_executor.completed or (queue and not queue.empty()):
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

            await execution_task

            if streaming_executor.error:
                raise streaming_executor.error

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
    diagram = payload.get('diagram', {})
    broadcast = payload.get('broadcast', True)
    return await run_diagram_endpoint(diagram=diagram, broadcast=broadcast)


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