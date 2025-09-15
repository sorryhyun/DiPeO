"""
Strawberry GraphQL scalar types for DiPeO.
Auto-generated from TypeScript branded types.

Generated at: 2025-09-15T11:20:50.509569
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
    HookID,
    NodeID,
    PersonID,
    CliSessionID,
    FileID,
    TaskID,
)


# Generate Strawberry scalar types for branded IDs

# Scalar type for ApiKeyID
ApiKeyIDScalar = strawberry.scalar(
    ApiKeyID,
    name="ApiKeyID",
    description="Scalar type for ApiKeyID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: ApiKeyID(v) if v is not None else None,
)

# Scalar type for ArrowID
ArrowIDScalar = strawberry.scalar(
    ArrowID,
    name="ArrowID",
    description="Scalar type for ArrowID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: ArrowID(v) if v is not None else None,
)

# Scalar type for DiagramID
DiagramIDScalar = strawberry.scalar(
    DiagramID,
    name="DiagramID",
    description="Scalar type for DiagramID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: DiagramID(v) if v is not None else None,
)

# Scalar type for ExecutionID
ExecutionIDScalar = strawberry.scalar(
    ExecutionID,
    name="ExecutionID",
    description="Scalar type for ExecutionID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: ExecutionID(v) if v is not None else None,
)

# Scalar type for HandleID
HandleIDScalar = strawberry.scalar(
    HandleID,
    name="HandleID",
    description="Scalar type for HandleID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: HandleID(v) if v is not None else None,
)

# Scalar type for HookID
HookIDScalar = strawberry.scalar(
    HookID,
    name="HookID",
    description="Scalar type for HookID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: HookID(v) if v is not None else None,
)

# Scalar type for NodeID
NodeIDScalar = strawberry.scalar(
    NodeID,
    name="NodeID",
    description="Scalar type for NodeID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: NodeID(v) if v is not None else None,
)

# Scalar type for PersonID
PersonIDScalar = strawberry.scalar(
    PersonID,
    name="PersonID",
    description="Scalar type for PersonID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: PersonID(v) if v is not None else None,
)

# Scalar type for CliSessionID
CliSessionIDScalar = strawberry.scalar(
    CliSessionID,
    name="CliSessionID",
    description="Scalar type for CliSessionID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: CliSessionID(v) if v is not None else None,
)

# Scalar type for FileID
FileIDScalar = strawberry.scalar(
    FileID,
    name="FileID",
    description="Scalar type for FileID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: FileID(v) if v is not None else None,
)

# Scalar type for TaskID
TaskIDScalar = strawberry.scalar(
    TaskID,
    name="TaskID",
    description="Scalar type for TaskID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: TaskID(v) if v is not None else None,
)


# Export all scalar types
__all__ = [
    "ApiKeyIDScalar",
    "ArrowIDScalar",
    "DiagramIDScalar",
    "ExecutionIDScalar",
    "HandleIDScalar",
    "HookIDScalar",
    "NodeIDScalar",
    "PersonIDScalar",
    "CliSessionIDScalar",
    "FileIDScalar",
    "TaskIDScalar",
]


# Convenience dictionary for looking up scalars by name
SCALAR_MAP = {
    "ApiKeyID": ApiKeyIDScalar,
    "ArrowID": ArrowIDScalar,
    "DiagramID": DiagramIDScalar,
    "ExecutionID": ExecutionIDScalar,
    "HandleID": HandleIDScalar,
    "HookID": HookIDScalar,
    "NodeID": NodeIDScalar,
    "PersonID": PersonIDScalar,
    "CliSessionID": CliSessionIDScalar,
    "FileID": FileIDScalar,
    "TaskID": TaskIDScalar,
}
