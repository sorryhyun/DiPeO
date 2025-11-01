import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dipeo.domain.base.exceptions import (
    ConfigurationError,
    DiPeOError,
    ExecutionError,
    ServiceError,
    ValidationError,
)


def setup_middleware(app: FastAPI):
    """Configure all middleware for the application."""
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Add MCP client origins (supports any MCP client)
    mcp_origins = os.environ.get("MCP_CLIENT_ORIGINS", "")
    if mcp_origins:
        origins.extend(mcp_origins.split(","))

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

    @app.exception_handler(DiPeOError)
    async def handle_agent_diagram_exception(request, exc: DiPeOError):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": exc.message, "details": exc.details},
        )
