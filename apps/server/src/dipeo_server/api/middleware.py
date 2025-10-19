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

    # In development, allow specific localhost origins
    # In production, you should configure this with your actual domain
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Add ChatGPT origins for MCP integration
    chatgpt_origins = os.environ.get("MCP_CHATGPT_ORIGINS", "")
    if chatgpt_origins:
        origins.extend(chatgpt_origins.split(","))

    # Default ChatGPT origins (if not configured)
    if not chatgpt_origins:
        origins.extend(
            [
                "https://chatgpt.com",
                "https://chat.openai.com",
            ]
        )

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
        """Global exception handler for application exceptions."""
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": exc.message, "details": exc.details},
        )
