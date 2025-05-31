"""Diagram router for tRPC-style API."""
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ...trpc import create_router, protected_procedure, TRPCContext
from ...services.diagram_service import DiagramService
from ...services.api_key_service import APIKeyService
from ...streaming.stream_manager import StreamManager
from ...exceptions import DiagramExecutionError
import uuid
import asyncio

# Input schemas
class ExecuteDiagramInput(BaseModel):
    diagram: Dict[str, Any]
    session_id: Optional[str] = None
    
class ValidateApiKeyInput(BaseModel):
    provider: str
    key: str

# Create diagram router
diagram_router = create_router()

@protected_procedure.mutation().input(ExecuteDiagramInput)
async def execute_diagram(ctx: TRPCContext, input_data: ExecuteDiagramInput):
    """Execute a diagram with hybrid client-server execution."""
    try:
        # Generate session ID if not provided
        session_id = input_data.session_id or str(uuid.uuid4())
        
        # Initialize services
        diagram_service = DiagramService()
        stream_manager = StreamManager()
        
        # Validate API keys are available
        if not ctx.api_keys:
            raise DiagramExecutionError("API keys required for diagram execution")
            
        # Start execution in background task
        task = asyncio.create_task(
            diagram_service.execute_diagram_hybrid(
                diagram=input_data.diagram,
                api_keys=ctx.api_keys,
                session_id=session_id,
                stream_manager=stream_manager
            )
        )
        
        return {
            "session_id": session_id,
            "status": "started",
            "message": "Diagram execution started"
        }
        
    except Exception as e:
        raise DiagramExecutionError(f"Failed to execute diagram: {str(e)}")

@protected_procedure.mutation().input(ValidateApiKeyInput)
async def validate_api_key(ctx: TRPCContext, input_data: ValidateApiKeyInput):
    """Validate an API key for a specific provider."""
    try:
        # Initialize API key service
        api_key_service = APIKeyService()
        
        # Validate the key
        is_valid = await api_key_service.validate_key(
            provider=input_data.provider,
            key=input_data.key
        )
        
        return {
            "valid": is_valid,
            "provider": input_data.provider
        }
        
    except Exception as e:
        return {
            "valid": False,
            "provider": input_data.provider,
            "error": str(e)
        }

# Add procedures to router
diagram_router.add_procedure("execute", execute_diagram)
diagram_router.add_procedure("validateApiKey", validate_api_key)