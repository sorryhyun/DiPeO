"""Main GraphQL schema definition for DiPeO."""
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from .queries import Query
from .mutations import Mutation
from .subscriptions import Subscription

# Create the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    # Enable schema introspection for development
    enable_query_introspection=True,
    # Add extensions for monitoring and optimization
    extensions=[
        # Add query depth limiter to prevent complex queries
        # QueryDepthLimiter(max_depth=10),
        # Add max tokens limiter
        # MaxTokensLimiter(max_tokens=5000),
    ]
)

# Create GraphQL router for FastAPI integration
def create_graphql_router(context_getter=None):
    """Create a GraphQL router with optional context."""
    return GraphQLRouter(
        schema,
        context_getter=context_getter,
        # Enable GraphQL playground UI
        graphiql=True,
        # Support both WebSocket protocols for subscriptions
        subscription_protocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
        ],
        # Path for GraphQL endpoint
        path="/graphql",
    )

# Export schema for code generation
if __name__ == "__main__":
    # This can be run to export the schema
    with open("schema.graphql", "w") as f:
        f.write(schema.as_str())