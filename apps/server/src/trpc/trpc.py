"""tRPC-style API for Python backend."""
from typing import Any, Dict, Optional, TypeVar, Callable
from fastapi import HTTPException, Request
from pydantic import BaseModel
import json

T = TypeVar('T')

class TRPCContext(BaseModel):
    """Context passed to all tRPC procedures."""
    request: Optional[Request] = None
    api_keys: Optional[Dict[str, str]] = None
    
class Procedure:
    """Base procedure class for tRPC-style endpoints."""
    
    def __init__(self, middleware: Optional[Callable] = None):
        self.middleware = middleware
        
    def input(self, schema: type[BaseModel]):
        """Add input validation to procedure."""
        def decorator(func: Callable):
            async def wrapper(context: TRPCContext, input_data: Dict[str, Any]):
                # Validate input
                try:
                    validated_input = schema(**input_data)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))
                    
                # Apply middleware if exists
                if self.middleware:
                    context = await self.middleware(context)
                    
                # Call actual function
                return await func(context, validated_input)
            
            wrapper._input_schema = schema
            wrapper._is_mutation = hasattr(self, '_is_mutation') and self._is_mutation
            return wrapper
        return decorator
    
    def mutation(self):
        """Mark procedure as mutation."""
        self._is_mutation = True
        return self
    
    def query(self):
        """Mark procedure as query."""
        self._is_mutation = False
        return self

def create_router():
    """Create a new tRPC router."""
    class Router:
        def __init__(self):
            self.procedures = {}
            
        def add_procedure(self, name: str, procedure: Callable):
            self.procedures[name] = procedure
            
        def merge(self, prefix: str, router: 'Router'):
            """Merge another router with prefix."""
            for name, proc in router.procedures.items():
                self.procedures[f"{prefix}.{name}"] = proc
                
    return Router()

# Middleware for protected procedures
async def auth_middleware(context: TRPCContext) -> TRPCContext:
    """Ensure API keys are available."""
    if not context.api_keys:
        raise HTTPException(status_code=401, detail="API keys required")
    return context

# Create procedure factories
public_procedure = Procedure()
protected_procedure = Procedure(middleware=auth_middleware)