"""Custom scalar types for DiPeO GraphQL schema."""

from typing import Any, NewType

import strawberry
from dipeo_domain import (
    ApiKeyID as _ApiKeyID,
)
from dipeo_domain import (
    ArrowID as _ArrowID,
)
from dipeo_domain import (
    DiagramID as _DiagramID,
)
from dipeo_domain import (
    ExecutionID as _ExecutionID,
)
from dipeo_domain import (
    HandleID as _HandleID,
)

# Import the canonical NewTypes from generated models
from dipeo_domain import (
    NodeID as _NodeID,
)
from dipeo_domain import (
    PersonID as _PersonID,
)

# Wrap the existing NewTypes as Strawberry scalars
NodeID = strawberry.scalar(_NodeID, description="Unique identifier for a node")

HandleID = strawberry.scalar(
    _HandleID, description="Unique identifier for a handle (format: nodeId:handleName)"
)

ArrowID = strawberry.scalar(_ArrowID, description="Unique identifier for an arrow")

PersonID = strawberry.scalar(
    _PersonID, description="Unique identifier for a person (LLM agent)"
)

ApiKeyID = strawberry.scalar(_ApiKeyID, description="Unique identifier for an API key")

ExecutionID = strawberry.scalar(
    _ExecutionID, description="Unique identifier for an execution"
)

DiagramID = strawberry.scalar(_DiagramID, description="Unique identifier for a diagram")

# JSON scalar for arbitrary data
JSONScalar = strawberry.scalar(
    NewType("JSONScalar", Any),
    description="Arbitrary JSON-serializable data",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)
