import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dipeo_server.shared.exceptions import AgentDiagramException


def setup_middleware(app: FastAPI):
    """Configure all middleware for the application."""

    # CORS middleware
    # In development, allow specific localhost origins
    # In production, you should configure this with your actual domain
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    # Add wildcard for development if needed
    if os.environ.get("ENVIRONMENT", "development") == "development":
        origins.append("*")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(AgentDiagramException)
    async def handle_agent_diagram_exception(request, exc: AgentDiagramException):
        """Global exception handler for application exceptions."""
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": exc.message, "details": exc.details},
        )
