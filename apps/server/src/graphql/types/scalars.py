"""Custom scalar types for DiPeO GraphQL schema."""
import strawberry
from typing import NewType

# Branded ID types for type safety
NodeID = strawberry.scalar(
    NewType("NodeID", str),
    description="Unique identifier for a node"
)

HandleID = strawberry.scalar(
    NewType("HandleID", str),
    description="Unique identifier for a handle (format: nodeId:handleName)"
)

ArrowID = strawberry.scalar(
    NewType("ArrowID", str),
    description="Unique identifier for an arrow"
)

PersonID = strawberry.scalar(
    NewType("PersonID", str),
    description="Unique identifier for a person (LLM agent)"
)

ApiKeyID = strawberry.scalar(
    NewType("ApiKeyID", str),
    description="Unique identifier for an API key"
)

ExecutionID = strawberry.scalar(
    NewType("ExecutionID", str),
    description="Unique identifier for an execution"
)

DiagramID = strawberry.scalar(
    NewType("DiagramID", str),
    description="Unique identifier for a diagram"
)