"""API Router configuration for DiPeO server."""

from dipeo.application.graphql import create_schema
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

from .context import get_request_context


def create_graphql_router(context_getter=None, container=None):
    """Create a GraphQL router with monitoring stream support."""
    from dipeo_server.app_context import get_container

    if not container:
        container = get_container()

    # Create the schema with the service registry
    schema = create_schema(container.registry)

    return GraphQLRouter(
        schema,
        context_getter=context_getter,
        graphiql=True,
        subscription_protocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
        ],
        path="/graphql",
        multipart_uploads_enabled=True,
    )


def setup_routes(app: FastAPI):
    """Configure all API routes for the application."""

    graphql_router = create_graphql_router(context_getter=get_request_context)
    app.include_router(graphql_router, prefix="")

    # V2 GraphQL router - temporarily disabled during migration
    # v2_graphql_router = create_v2_graphql_router(context_getter=get_request_context)
    # app.include_router(v2_graphql_router, prefix="")
