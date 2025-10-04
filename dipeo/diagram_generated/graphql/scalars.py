"""
Strawberry GraphQL scalar types for DiPeO.
Auto-generated from TypeScript branded types.

Generated at: 2025-10-04T12:21:26.051922
"""

import strawberry
from typing import Any, NewType
from strawberry.scalars import ID

# Debug info:
# scalars defined: yes

# scalars type: list
# scalars value: [{'name': 'CliSessionID', 'type': 'string', 'description': 'Branded scalar type for...


# Import the base domain types

from dipeo.diagram_generated.domain_models import (
    CliSessionID,
    NodeID,
    ArrowID,
    HandleID,
    PersonID,
    ApiKeyID,
    DiagramID,
    HookID,
    TaskID,
    ExecutionID,
    FileID,
)



# Generate Strawberry scalar types for branded IDs


# Branded scalar type for CliSessionID
CliSessionIDScalar = strawberry.scalar(
    CliSessionID,
    name="CliSessionID",
    description="Branded scalar type for CliSessionID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: CliSessionID(v) if v is not None else None,
)

# Branded scalar type for NodeID
NodeIDScalar = strawberry.scalar(
    NodeID,
    name="NodeID",
    description="Branded scalar type for NodeID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: NodeID(v) if v is not None else None,
)

# Branded scalar type for ArrowID
ArrowIDScalar = strawberry.scalar(
    ArrowID,
    name="ArrowID",
    description="Branded scalar type for ArrowID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: ArrowID(v) if v is not None else None,
)

# Branded scalar type for HandleID
HandleIDScalar = strawberry.scalar(
    HandleID,
    name="HandleID",
    description="Branded scalar type for HandleID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: HandleID(v) if v is not None else None,
)

# Branded scalar type for PersonID
PersonIDScalar = strawberry.scalar(
    PersonID,
    name="PersonID",
    description="Branded scalar type for PersonID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: PersonID(v) if v is not None else None,
)

# Branded scalar type for ApiKeyID
ApiKeyIDScalar = strawberry.scalar(
    ApiKeyID,
    name="ApiKeyID",
    description="Branded scalar type for ApiKeyID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: ApiKeyID(v) if v is not None else None,
)

# Branded scalar type for DiagramID
DiagramIDScalar = strawberry.scalar(
    DiagramID,
    name="DiagramID",
    description="Branded scalar type for DiagramID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: DiagramID(v) if v is not None else None,
)

# Branded scalar type for HookID
HookIDScalar = strawberry.scalar(
    HookID,
    name="HookID",
    description="Branded scalar type for HookID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: HookID(v) if v is not None else None,
)

# Branded scalar type for TaskID
TaskIDScalar = strawberry.scalar(
    TaskID,
    name="TaskID",
    description="Branded scalar type for TaskID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: TaskID(v) if v is not None else None,
)

# Branded scalar type for ExecutionID
ExecutionIDScalar = strawberry.scalar(
    ExecutionID,
    name="ExecutionID",
    description="Branded scalar type for ExecutionID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: ExecutionID(v) if v is not None else None,
)

# Branded scalar type for FileID
FileIDScalar = strawberry.scalar(
    FileID,
    name="FileID",
    description="Branded scalar type for FileID",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: FileID(v) if v is not None else None,
)



# Export all scalar types
__all__ = [

    "CliSessionIDScalar",
    "NodeIDScalar",
    "ArrowIDScalar",
    "HandleIDScalar",
    "PersonIDScalar",
    "ApiKeyIDScalar",
    "DiagramIDScalar",
    "HookIDScalar",
    "TaskIDScalar",
    "ExecutionIDScalar",
    "FileIDScalar",

]


# Convenience dictionary for looking up scalars by name
SCALAR_MAP = {

    "CliSessionID": CliSessionIDScalar,
    "NodeID": NodeIDScalar,
    "ArrowID": ArrowIDScalar,
    "HandleID": HandleIDScalar,
    "PersonID": PersonIDScalar,
    "ApiKeyID": ApiKeyIDScalar,
    "DiagramID": DiagramIDScalar,
    "HookID": HookIDScalar,
    "TaskID": TaskIDScalar,
    "ExecutionID": ExecutionIDScalar,
    "FileID": FileIDScalar,

}
