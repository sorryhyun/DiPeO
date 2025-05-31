"""tRPC integration endpoint for FastAPI."""
from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Any
from ...trpc import TRPCContext, app_router as trpc_app_router
from ...services.api_key_service import APIKeyService
import json

router = APIRouter()

def get_api_keys():
    """Get API keys from service."""
    service = APIKeyService()
    return {key["id"]: key for key in service.list_api_keys()}

@router.post("/trpc/{procedure:path}")
async def trpc_handler(
    procedure: str, 
    request: Request,
    api_keys: Dict[str, Any] = Depends(get_api_keys)
):
    """Handle tRPC procedure calls."""
    try:
        # Parse request body
        body = await request.json()
        
        # Create context
        context = TRPCContext(
            request=request,
            api_keys=api_keys
        )
        
        # Find and execute procedure
        if procedure not in trpc_app_router.procedures:
            raise HTTPException(status_code=404, detail=f"Procedure {procedure} not found")
            
        proc = trpc_app_router.procedures[procedure]
        
        # Execute procedure
        result = await proc(context, body.get("input", {}))
        
        return {
            "result": {
                "data": result
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trpc")
async def trpc_info():
    """Get available tRPC procedures."""
    procedures = []
    for name, proc in trpc_app_router.procedures.items():
        procedures.append({
            "name": name,
            "type": "mutation" if hasattr(proc, "_is_mutation") and proc._is_mutation else "query"
        })
    
    return {
        "procedures": procedures
    }