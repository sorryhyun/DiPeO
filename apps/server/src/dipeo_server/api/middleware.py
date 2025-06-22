from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dipeo_server.core.exceptions import AgentDiagramException


def setup_middleware(app: FastAPI):
    """Configure all middleware for the application."""

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(AgentDiagramException)
    async def handle_agent_diagram_exception(request, exc: AgentDiagramException):
        """Global exception handler for application exceptions."""
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": exc.message, "details": exc.details},
        )
