"""Custom scalar types for DiPeO GraphQL schema."""
import strawberry
from typing import NewType, Any

# Import the canonical NewTypes from generated models
from dipeo_domain import (
    NodeID as _NodeID,
    HandleID as _HandleID,
    ArrowID as _ArrowID,
    PersonID as _PersonID,
    ApiKeyID as _ApiKeyID,
    ExecutionID as _ExecutionID,
    DiagramID as _DiagramID
)

# Wrap the existing NewTypes as Strawberry scalars
NodeID = strawberry.scalar(
    _NodeID,
    description="Unique identifier for a node"
)

HandleID = strawberry.scalar(
    _HandleID,
    description="Unique identifier for a handle (format: nodeId:handleName)"
)

ArrowID = strawberry.scalar(
    _ArrowID,
    description="Unique identifier for an arrow"
)

PersonID = strawberry.scalar(
    _PersonID,
    description="Unique identifier for a person (LLM agent)"
)

ApiKeyID = strawberry.scalar(
    _ApiKeyID,
    description="Unique identifier for an API key"
)

ExecutionID = strawberry.scalar(
    _ExecutionID,
    description="Unique identifier for an execution"
)

DiagramID = strawberry.scalar(
    _DiagramID,
    description="Unique identifier for a diagram"
)

# JSON scalar for arbitrary data
JSONScalar = strawberry.scalar(
    NewType("JSONScalar", Any),
    description="Arbitrary JSON-serializable data",
    serialize=lambda v: v,
    parse_value=lambda v: v
)