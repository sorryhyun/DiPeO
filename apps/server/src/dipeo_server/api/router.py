"""API Router configuration for DiPeO server."""

from fastapi import FastAPI

from .graphql.context import get_graphql_context
from .graphql.schema import create_unified_graphql_router as create_graphql_router
from .graphql.v2.schema import create_v2_graphql_router


def setup_routes(app: FastAPI):
    # Configure all API routes for the application

    # GraphQL router (current)
    graphql_router = create_graphql_router(context_getter=get_graphql_context)
    app.include_router(graphql_router, prefix="")
    
    # GraphQL v2 router (new interface-based design)
    graphql_v2_router = create_v2_graphql_router(context_getter=get_graphql_context)
    app.include_router(graphql_v2_router, prefix="")

    # Future REST API routes can be added here
