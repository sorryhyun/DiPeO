"""Main GraphQL schema definition for DiPeO."""
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

from .queries import Query
from . import Mutation_mutation as Mutation
from .subscriptions import Subscription

# Create the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[]
)

# Create GraphQL router for FastAPI integration
def create_graphql_router(context_getter=None):
    """Create a GraphQL router with optional context."""
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
    
    output_path = sys.argv[1] if len(sys.argv) > 1 else "schema.graphql"
    schema_str = schema.as_str()
    
    with open(output_path, "w") as f:
        f.write(schema_str)
    
    print(f"GraphQL schema exported to {output_path}")
    print(f"Schema length: {len(schema_str)} characters")