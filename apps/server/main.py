import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse, StreamingResponse
import uvicorn
from dotenv import load_dotenv
import json
import asyncio
from typing import AsyncGenerator, List
import traceback
from typing import Optional
from datetime import datetime
import inspect

from src.services.memory_service import MemoryService
from src.exceptions import AgentDiagramException
from src.run_graph import DiagramExecutor
from src.services.api_key_service import APIKeyService
from src.services.llm_service import LLMService
from src.services.diagram_service import DiagramService
from src.utils.dependencies import (
    get_api_key_service, get_llm_service, get_diagram_service, 
    get_unified_file_service, get_memory_service
)
from src.utils.diagram_migrator import DiagramMigrator
from config import BASE_DIR, CONVERSATION_LOG_DIR

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


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

# apps/server/main.py
from fastapi import WebSocket, WebSocketDisconnect
from src.streaming.stream_manager import stream_manager


class StreamingExecutor:
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    yield
    pass


app = FastAPI(
    title="AgentDiagram Backend",
    description="API server for AgentDiagram frontend",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await stream_manager.connect_websocket(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "subscribe_execution":
                execution_id = data["execution_id"]
                await stream_manager.subscribe_to_execution(client_id, execution_id)
    except WebSocketDisconnect:
        await stream_manager.disconnect_websocket(client_id)

@app.exception_handler(AgentDiagramException)
async def handle_agent_diagram_exception(request, exc: AgentDiagramException):
    """Global exception handler for application exceptions."""
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": exc.message, "details": exc.details}
    )

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/import-uml")
async def import_uml(
    payload: dict, 
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Import UML text and return a diagram state."""
    uml_text = payload.get('uml', '')
    return diagram_service.import_uml(uml_text)


@app.post("/api/import-yaml") 
async def import_yaml(
    payload: dict,
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Import YAML agent definitions and return a diagram state."""
    yaml_text = payload.get('yaml', '')
    return diagram_service.import_yaml(yaml_text)


@app.post("/api/export-uml")
async def export_uml(
    diagram: dict,
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Export a diagram state to UML text."""
    uml_text = diagram_service.export_uml(diagram)
    return PlainTextResponse(content=uml_text, media_type='text/plain')


@app.post("/api/save")
async def save_content(
        payload: dict,
        unified_file_service=Depends(get_unified_file_service),
        diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Unified save endpoint for diagrams and UML export."""
    content = payload.get('content') or payload.get('diagram')
    filename = payload.get('filename', 'output.json')
    format_type = payload.get('format', 'json')

    if not content:
        raise HTTPException(status_code=400, detail="No content or diagram provided")

    if format_type == 'uml':
        content = diagram_service.export_uml(content)
        if not filename.endswith('.puml'):
            filename = filename.rsplit('.', 1)[0] + '.puml'
    elif format_type == 'json' and not filename.endswith('.json'):
        filename = filename.rsplit('.', 1)[0] + '.json'

    try:
        # Note the await here - this is important!
        relative_path = await unified_file_service.write(
            path=filename,
            content=content,
            relative_to="base",
            format=format_type if format_type != 'uml' else 'text'
        )
        return {"success": True, "message": f"File saved to {relative_path}", "path": relative_path}
    except Exception as e:
        # Log the actual error for debugging
        import traceback
        traceback.print_exc()
        # Return JSON error response instead of raising HTTPException
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "detail": "Failed to save file"}
        )



@app.post("/api/run-diagram")
async def run_diagram_endpoint(diagram: dict, broadcast: bool=True):
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

@app.post("/api/external/run-diagram")
async def external_run_diagram(diagram: dict):
    """API endpoint for external services - always broadcasts to connected browsers"""
    return await run_diagram_endpoint(diagram, broadcast=True)

@app.post("/api/run-diagram-sync")
async def run_diagram_sync_endpoint(
    diagram: dict,
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    try:
        return await diagram_service.run_diagram_sync(diagram, CONVERSATION_LOG_DIR)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        # Log the full traceback for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/diagram-stats")
async def get_diagram_stats(diagram: dict):
    """Get statistics about a diagram without executing it."""
    try:
        diagram = DiagramMigrator.migrate(diagram)
        
        nodes = diagram.get("nodes", [])
        arrows = diagram.get("arrows", [])
        persons = diagram.get("persons", [])

        node_types = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

        return {
            "node_count": len(nodes),
            "arrow_count": len(arrows),
            "person_count": len(persons),
            "node_types": node_types,
            "estimated_execution_time": len(nodes) * 2
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def list_models(
    service: str, 
    apiKeyId: str,
    llm_service: LLMService = Depends(get_llm_service)
):
    """Return available model names for the given service & key."""
    models = await llm_service.get_available_models(service, apiKeyId)
    return {"models": models}


@app.get("/api/apikeys")
async def list_api_keys(
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """List stored API keys (without revealing raw secrets)."""
    api_keys = api_key_service.list_api_keys()
    return {"apiKeys": api_keys}


@app.post("/api/apikeys")
async def create_api_key(
    payload: dict,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Create a new API key entry."""
    name = payload.get("name")
    service = payload.get("service") 
    raw_key = payload.get("key")
    
    result = api_key_service.create_api_key(name, service, raw_key)
    return result


@app.delete("/api/apikeys/{key_id}")
async def delete_api_key_endpoint(
    key_id: str,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Delete an existing API key by ID."""
    api_key_service.delete_api_key(key_id)
    return JSONResponse(content='', status_code=204)

from fastapi import File, UploadFile


@app.post("/api/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    unified_file_service = Depends(get_unified_file_service)
):
    """Save an uploaded file and return its relative path."""
    try:
        content = await file.read()
        
        relative_path = unified_file_service.write(
            path=file.filename,
            content=content.decode('utf-8') if isinstance(content, bytes) else content,
            relative_to="uploads"
        )
        
        return {"success": True, "path": relative_path, "message": f"File uploaded to {relative_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/llm")
async def call_llm(
    payload: dict,
    llm_service: LLMService = Depends(get_llm_service)
):
    """Proxy endpoint for LLM calls."""
    text, cost = await llm_service.call_llm(
        payload.get("service"),
        payload.get("apiKeyId"),
        payload.get("model"),
        payload.get("messages"),
        payload.get("systemPrompt", "")
    )
    return {"text": text, "cost": cost}


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi.responses import Response
        
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    except ImportError:
        # If prometheus_client is not installed, return a simple message
        return {"message": "Prometheus client not installed. Install with: pip install prometheus-client"}

@app.get("/api/conversations")
async def get_conversations(
    personId: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    executionId: Optional[str] = None,
    showForgotten: bool = False,
    startTime: Optional[str] = None,
    endTime: Optional[str] = None,
    since: Optional[str] = None,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get conversation data with pagination and filtering."""
    try:
        persons_data = {}

        if personId:
            person_ids = [personId]
        else:
            person_ids = memory_service.get_all_participants_in_conversation()

        for pid in person_ids:
            person_memory = memory_service.get_or_create_person_memory(pid)

            filtered_messages = []
            for msg in person_memory.messages:
                if not showForgotten and msg.id in person_memory.forgotten_message_ids:
                    continue

                if search and search.lower() not in msg.content.lower():
                    continue

                if executionId and msg.execution_id != executionId:
                    continue

                if startTime:
                    start_dt = datetime.fromisoformat(startTime)
                    if msg.timestamp < start_dt:
                        continue

                if endTime:
                    end_dt = datetime.fromisoformat(endTime)
                    if msg.timestamp > end_dt:
                        continue

                if since:
                    since_dt = datetime.fromisoformat(since)
                    if msg.timestamp <= since_dt:
                        continue

                filtered_messages.append(msg)

            filtered_messages.sort(key=lambda m: m.timestamp)

            paginated_messages = filtered_messages[offset:offset + limit]

            formatted_messages = []
            for msg in paginated_messages:
                formatted_msg = msg.to_dict()

                if hasattr(msg, 'node_id'):
                    formatted_msg['node_id'] = msg.node_id
                    formatted_msg['node_label'] = msg.node_label

                if hasattr(msg, 'token_count'):
                    formatted_msg['token_count'] = msg.token_count
                if hasattr(msg, 'cost'):
                    formatted_msg['cost'] = msg.cost

                formatted_messages.append(formatted_msg)

            persons_data[pid] = {
                "person_id": pid,
                "messages": formatted_messages,
                "total_messages": len(person_memory.messages),
                "visible_messages": len([m for m in person_memory.messages
                                         if m.id not in person_memory.forgotten_message_ids]),
                "forgotten_messages": len(person_memory.forgotten_message_ids),
                "has_more": len(filtered_messages) > offset + limit
            }

        return {"persons": persons_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/clear")
async def clear_conversations(
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Clear all conversation memory."""
    try:
        memory_service.clear_all_memory()
        return {"success": True, "message": "All conversations cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)