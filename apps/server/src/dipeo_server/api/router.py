"""API Router configuration for DiPeO server."""

from fastapi import FastAPI
from .schema import create_graphql_router
from .context import get_graphql_context


def setup_routes(app: FastAPI):
    """Configure all API routes for the application."""
    
    # GraphQL router
    graphql_router = create_graphql_router(context_getter=get_graphql_context)
    app.include_router(graphql_router, prefix="")
    
    # Future REST API routes can be added here