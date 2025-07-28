"""Unified GraphQL schema with direct streaming support."""

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

# Import schema from application layer
from dipeo.application.graphql import create_schema
from dipeo.application.unified_service_registry import UnifiedServiceRegistry

# The schema will be created with the service registry in create_unified_graphql_router
unified_schema = None


def create_unified_graphql_router(context_getter=None, container=None):
    # Create a GraphQL router with direct streaming support
    
    # If container is provided, use it directly
    if container:
        registry = container.application.service_registry()
    else:
        # Try to get container (may fail during import)
        try:
            from dipeo_server.application.app_context import get_container
            container = get_container()
            registry = container.application.service_registry()
        except RuntimeError:
            # Container not initialized yet, create a mock registry for now
            # This will be replaced when the router is actually used
            registry = UnifiedServiceRegistry()
    
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


# Export schema for code generation
if __name__ == "__main__":
    import sys
    
    # Create a mock registry for schema export
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    registry = UnifiedServiceRegistry()
    
    # Create schema with mock registry
    schema = create_schema(registry)
    schema_str = schema.as_str()

    # If output path is provided as argument, write to file
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
        with open(output_path, "w") as f:
            f.write(schema_str)
        print(f"Unified GraphQL schema exported to {output_path}", file=sys.stderr)
        print(f"Schema length: {len(schema_str)} characters", file=sys.stderr)
    else:
        # Otherwise, print to stdout for piping
        print(schema_str)
