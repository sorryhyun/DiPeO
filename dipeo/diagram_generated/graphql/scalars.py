"""
Strawberry GraphQL scalar types for DiPeO.
Auto-generated from TypeScript branded types.

Generated at: 2025-09-08T16:41:30.558487
"""

import strawberry
from typing import Any, NewType
from strawberry.scalars import ID

# Import the base domain types
from dipeo.diagram_generated.domain_models import (
    ApiKeyID,
    ArrowID,
    DiagramID,
    ExecutionID,
    HandleID,
    NodeID,
    PersonID,
)


# Generate Strawberry scalar types for branded IDs

# Unique identifier type for apikey entities
ApiKeyIDScalar = strawberry.scalar(
    ApiKeyID,
    name="ApiKeyID",
    description="Unique identifier type for apikey entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: ApiKeyID(v) if v is not None else None,
)

# Unique identifier type for arrow entities
ArrowIDScalar = strawberry.scalar(
    ArrowID,
    name="ArrowID",
    description="Unique identifier type for arrow entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: ArrowID(v) if v is not None else None,
)

# Unique identifier type for diagram entities
DiagramIDScalar = strawberry.scalar(
    DiagramID,
    name="DiagramID",
    description="Unique identifier type for diagram entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: DiagramID(v) if v is not None else None,
)

# Unique identifier type for execution entities
ExecutionIDScalar = strawberry.scalar(
    ExecutionID,
    name="ExecutionID",
    description="Unique identifier type for execution entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: ExecutionID(v) if v is not None else None,
)

# Unique identifier type for handle entities
HandleIDScalar = strawberry.scalar(
    HandleID,
    name="HandleID",
    description="Unique identifier type for handle entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: HandleID(v) if v is not None else None,
)

# Unique identifier type for node entities
NodeIDScalar = strawberry.scalar(
    NodeID,
    name="NodeID",
    description="Unique identifier type for node entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: NodeID(v) if v is not None else None,
)

# Unique identifier type for person entities
PersonIDScalar = strawberry.scalar(
    PersonID,
    name="PersonID",
    description="Unique identifier type for person entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: PersonID(v) if v is not None else None,
)


# Export all scalar types
__all__ = [
    "ApiKeyIDScalar",
    "ArrowIDScalar",
    "DiagramIDScalar",
    "ExecutionIDScalar",
    "HandleIDScalar",
    "NodeIDScalar",
    "PersonIDScalar",
]


# Convenience dictionary for looking up scalars by name
SCALAR_MAP = {
    "ApiKeyID": ApiKeyIDScalar,
    "ArrowID": ArrowIDScalar,
    "DiagramID": DiagramIDScalar,
    "ExecutionID": ExecutionIDScalar,
    "HandleID": HandleIDScalar,
    "NodeID": NodeIDScalar,
    "PersonID": PersonIDScalar,
}
