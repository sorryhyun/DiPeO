"""Unified GraphQL schema with direct streaming support."""

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.schema.config import StrawberryConfig

from .mutations import Mutation
from .queries import Query
from .subscriptions import Subscription

# Create unified schema with direct streaming subscriptions
# Disable auto camelCase conversion to keep snake_case field names
unified_schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[],
    config=StrawberryConfig(auto_camel_case=False),
)


def create_unified_graphql_router(context_getter=None):
    # Create a GraphQL router with direct streaming support
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

    schema_str = unified_schema.as_str()

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
