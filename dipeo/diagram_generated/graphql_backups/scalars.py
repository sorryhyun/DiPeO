"""
Strawberry GraphQL scalar types for DiPeO.
Auto-generated from TypeScript branded types.

Generated at: 2025-09-13T13:11:46.471538
"""

import strawberry
from typing import Any, NewType
from strawberry.scalars import ID

# Import the base domain types
from dipeo.diagram_generated.domain_models import (
    ApiKeyID,
    ArrowID,
    CliSessionID,
    DiagramID,
    ExecutionID,
    FileID,
    HandleID,
    HookID,
    NodeID,
    PersonID,
    TaskID,
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

# Unique identifier type for clisession entities
CliSessionIDScalar = strawberry.scalar(
    CliSessionID,
    name="CliSessionID",
    description="Unique identifier type for clisession entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: CliSessionID(v) if v is not None else None,
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

# Unique identifier type for file entities
FileIDScalar = strawberry.scalar(
    FileID,
    name="FileID",
    description="Unique identifier type for file entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: FileID(v) if v is not None else None,
)

# Unique identifier type for handle entities
HandleIDScalar = strawberry.scalar(
    HandleID,
    name="HandleID",
    description="Unique identifier type for handle entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: HandleID(v) if v is not None else None,
)

# Unique identifier type for hook entities
HookIDScalar = strawberry.scalar(
    HookID,
    name="HookID",
    description="Unique identifier type for hook entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: HookID(v) if v is not None else None,
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

# Unique identifier type for task entities
TaskIDScalar = strawberry.scalar(
    TaskID,
    name="TaskID",
    description="Unique identifier type for task entities",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: TaskID(v) if v is not None else None,
)


# Export all scalar types
__all__ = [
    "ApiKeyIDScalar",
    "ArrowIDScalar",
    "CliSessionIDScalar",
    "DiagramIDScalar",
    "ExecutionIDScalar",
    "FileIDScalar",
    "HandleIDScalar",
    "HookIDScalar",
    "NodeIDScalar",
    "PersonIDScalar",
    "TaskIDScalar",
]


# Convenience dictionary for looking up scalars by name
SCALAR_MAP = {
    "ApiKeyID": ApiKeyIDScalar,
    "ArrowID": ArrowIDScalar,
    "CliSessionID": CliSessionIDScalar,
    "DiagramID": DiagramIDScalar,
    "ExecutionID": ExecutionIDScalar,
    "FileID": FileIDScalar,
    "HandleID": HandleIDScalar,
    "HookID": HookIDScalar,
    "NodeID": NodeIDScalar,
    "PersonID": PersonIDScalar,
    "TaskID": TaskIDScalar,
}
