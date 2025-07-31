"""API Router configuration for DiPeO server."""

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

# Import schema creation from application layer
from dipeo.application.graphql import create_schema

from .context import get_request_context


def create_graphql_router(context_getter=None, container=None):
    """Create a GraphQL router with direct streaming support."""
    from dipeo_server.application.app_context import get_container

    # Always use the container from app context if not provided
    if not container:
        container = get_container()

    # Create the schema with the service registry
    schema = create_schema(container.registry)

    return GraphQLRouter(
        schema,
        context_getter=context_getter,
        # Enable GraphQL playground UI
        graphiql=True,
        # Support modern WebSocket protocol for subscriptions
        subscription_protocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
        ],
        # Path for GraphQL endpoint
        path="/graphql",
        # Enable multipart uploads (for file upload support)
        multipart_uploads_enabled=True,
    )



def setup_routes(app: FastAPI):
    """Configure all API routes for the application."""

    # GraphQL router
    graphql_router = create_graphql_router(context_getter=get_request_context)
    app.include_router(graphql_router, prefix="")

    # V2 GraphQL router - temporarily disabled during migration
    # v2_graphql_router = create_v2_graphql_router(context_getter=get_request_context)
    # app.include_router(v2_graphql_router, prefix="")

    # SSE router for direct streaming
    from .sse import router as sse_router
    app.include_router(sse_router)

    # Future REST API routes can be added here
