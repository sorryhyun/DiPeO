"""
Diagram V2 API - Enhanced execution endpoints using unified backend engine
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List
import json
import logging
import asyncio
from datetime import datetime

from ...services.unified_execution_engine import UnifiedExecutionEngine
from ...services.llm_service import LLMService
from ...services.unified_file_service import UnifiedFileService
from ...services.api_key_service import APIKeyService
from ...utils.dependencies import get_llm_service, get_unified_file_service, get_api_key_service
from ...core import handle_api_errors
from ...exceptions import DiagramExecutionError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["diagram-v2"])


@router.post("/run-diagram")
@handle_api_errors
async def run_diagram_v2(
    diagram: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None,
    llm_service: LLMService = Depends(get_llm_service),
    file_service: UnifiedFileService = Depends(get_unified_file_service),
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


@router.get("/executions/{execution_id}")
@handle_api_errors
async def get_execution_details(
    execution_id: str,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """Get details about a specific execution"""
    # TODO: Implement execution state persistence
    # For now, return a placeholder response
    return {
        "execution_id": execution_id,
        "status": "unknown",
        "message": "Execution state persistence not yet implemented"
    }


@router.get("/executions/{execution_id}/state")
@handle_api_errors
async def get_execution_state(
    execution_id: str
):
    """Get current state of an execution"""
    # TODO: Implement execution state management
    return {
        "execution_id": execution_id,
        "state": "unknown",
        "message": "Execution state management not yet implemented"
    }


@router.post("/executions/{execution_id}/pause")
@handle_api_errors
async def pause_execution(
    execution_id: str
):
    """Pause an execution"""
    # TODO: Implement execution pause/resume
    return {
        "execution_id": execution_id,
        "action": "pause",
        "message": "Execution pause/resume not yet implemented"
    }


@router.post("/executions/{execution_id}/resume")
@handle_api_errors
async def resume_execution(
    execution_id: str
):
    """Resume a paused execution"""
    # TODO: Implement execution pause/resume
    return {
        "execution_id": execution_id,
        "action": "resume", 
        "message": "Execution pause/resume not yet implemented"
    }


@router.get("/execution-capabilities")
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


@router.get("/health")
@handle_api_errors
async def health_check():
    """Health check endpoint for V2 API"""
    return {
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }