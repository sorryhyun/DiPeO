"""API Router configuration for DiPeO server."""

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from .graphql.context import get_graphql_context
from .graphql.schema import create_unified_graphql_router as create_graphql_router


def create_v2_graphql_router(context_getter=None, container=None):
    """Create v2 GraphQL router with interface-based schema."""
    from dipeo.application.graphql.v2 import create_v2_schema
    from dipeo.application.registry import ServiceRegistry

    # Get service registry
    if container:
        registry = container.application.service_registry()
    else:
        try:
            from dipeo_server.application.app_context import get_container

            container = get_container()
            registry = container.application.service_registry()
        except RuntimeError:
            registry = ServiceRegistry()

    # Create the v2 schema with service registry
    schema = create_v2_schema(service_registry=registry)

    return GraphQLRouter(
        schema,
        context_getter=context_getter,
        graphiql=True,
        path="/v2/graphql",
    )


def setup_routes(app: FastAPI):
    # Configure all API routes for the application

    # GraphQL router
    graphql_router = create_graphql_router(context_getter=get_graphql_context)
    app.include_router(graphql_router, prefix="")

    # V2 GraphQL router - temporarily disabled during migration
    # v2_graphql_router = create_v2_graphql_router(context_getter=get_graphql_context)
    # app.include_router(v2_graphql_router, prefix="")

    # SSE router for direct streaming
    from .sse import router as sse_router
    app.include_router(sse_router)

    # Future REST API routes can be added here
