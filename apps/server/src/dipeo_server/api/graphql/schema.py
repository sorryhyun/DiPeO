"""Unified GraphQL schema with direct streaming support."""

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

from .mutations import Mutation
from .queries import Query
from .subscriptions import Subscription

# Create unified schema with direct streaming subscriptions
unified_schema = strawberry.Schema(
    query=Query, mutation=Mutation, subscription=Subscription, extensions=[]
)


def create_unified_graphql_router(context_getter=None):
    """Create a GraphQL router with direct streaming support."""
    return GraphQLRouter(
        unified_schema,
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

    output_path = sys.argv[1] if len(sys.argv) > 1 else "unified_schema.graphql"
    schema_str = unified_schema.as_str()

    with open(output_path, "w") as f:
        f.write(schema_str)

    print(f"Unified GraphQL schema exported to {output_path}")
    print(f"Schema length: {len(schema_str)} characters")
