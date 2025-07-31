"""GraphQL router creation for the DiPeO server.

This module creates the GraphQL router for serving the schema from the application layer.
The actual schema definition lives in dipeo.application.graphql.
"""

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

# Import schema from application layer
from dipeo.application.graphql import create_schema
from dipeo.application.registry import ServiceRegistry

# The schema will be created with the service registry in create_unified_graphql_router
unified_schema = None


def create_unified_graphql_router(context_getter=None, container=None):
    # Create a GraphQL router with direct streaming support

    # If container is provided, use it directly
    if container:
        registry = container.registry
    else:
        # Try to get container (may fail during import)
        try:
            from dipeo_server.application.app_context import get_container

            container = get_container()
            registry = container.registry
        except RuntimeError:
            # Container not initialized yet, create a mock registry for now
            # This will be replaced when the router is actually used
            registry = ServiceRegistry()

    # Create the schema with the injected registry
    schema = create_schema(registry)

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


# Note: Schema export functionality has been moved to dipeo.application.graphql.export_schema
# This keeps the server layer focused on HTTP/WebSocket concerns only
