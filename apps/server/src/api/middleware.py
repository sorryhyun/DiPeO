from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..exceptions import AgentDiagramException
from .config import ENABLE_DEPRECATED_REST

# Import deprecation middleware only if the module exists
try:
    from .middleware_module.deprecation import DeprecationMiddleware
    HAS_DEPRECATION_MIDDLEWARE = True
except ImportError:
    HAS_DEPRECATION_MIDDLEWARE = False


def setup_middleware(app: FastAPI):
    """Configure all middleware for the application."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add deprecation middleware if REST endpoints are enabled
    if ENABLE_DEPRECATED_REST and HAS_DEPRECATION_MIDDLEWARE:
        app.add_middleware(DeprecationMiddleware)
    
    # Exception handlers
    @app.exception_handler(AgentDiagramException)
    async def handle_agent_diagram_exception(request, exc: AgentDiagramException):
        """Global exception handler for application exceptions."""
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": exc.message, "details": exc.details}
        )