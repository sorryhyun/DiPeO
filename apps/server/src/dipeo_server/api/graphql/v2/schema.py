"""GraphQL v2 schema with interface-based node design."""

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.schema.config import StrawberryConfig
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

from .types import Query, Mutation, Subscription


# Create v2 schema with interface-based design
schema_v2 = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[],
    config=StrawberryConfig(auto_camel_case=False),
)


def create_v2_graphql_router(context_getter=None):
    """Create GraphQL v2 router with new interface-based schema."""
    return GraphQLRouter(
        schema_v2,
        context_getter=context_getter,
        graphiql=True,
        subscription_protocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
        ],
        path="/v2/graphql",
        multipart_uploads_enabled=True,
    )


# Export schema for code generation
if __name__ == "__main__":
    import sys

    schema_str = schema_v2.as_str()

    if len(sys.argv) > 1:
        output_path = sys.argv[1]
        with open(output_path, "w") as f:
            f.write(schema_str)
        print(f"GraphQL v2 schema exported to {output_path}", file=sys.stderr)
        print(f"Schema length: {len(schema_str)} characters", file=sys.stderr)
    else:
        print(schema_str)