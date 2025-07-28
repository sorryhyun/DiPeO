"""
Strawberry scalar types for DiPeO IDs.

This module registers all the NewType ID types as Strawberry scalars.
"""

import strawberry
from dipeo.diagram_generated.domain_models import (
    NodeID,
    HandleID,
    ArrowID,
    PersonID,
    ApiKeyID,
    DiagramID,
    ExecutionID,
    HookID,
    TaskID,
)

# Register ID types as Strawberry scalars
NodeIDScalar = strawberry.scalar(
    NodeID,
    name="NodeID",
    description="Unique identifier for nodes",
    serialize=lambda v: str(v),
    parse_value=lambda v: NodeID(str(v)) if v else None,
)

HandleIDScalar = strawberry.scalar(
    HandleID,
    name="HandleID",
    description="Unique identifier for handles",
    serialize=lambda v: str(v),
    parse_value=lambda v: HandleID(str(v)) if v else None,
)

ArrowIDScalar = strawberry.scalar(
    ArrowID,
    name="ArrowID",
    description="Unique identifier for arrows",
    serialize=lambda v: str(v),
    parse_value=lambda v: ArrowID(str(v)) if v else None,
)

PersonIDScalar = strawberry.scalar(
    PersonID,
    name="PersonID",
    description="Unique identifier for persons",
    serialize=lambda v: str(v),
    parse_value=lambda v: PersonID(str(v)) if v else None,
)

ApiKeyIDScalar = strawberry.scalar(
    ApiKeyID,
    name="ApiKeyID",
    description="Unique identifier for API keys",
    serialize=lambda v: str(v),
    parse_value=lambda v: ApiKeyID(str(v)) if v else None,
)

DiagramIDScalar = strawberry.scalar(
    DiagramID,
    name="DiagramID",
    description="Unique identifier for diagrams",
    serialize=lambda v: str(v),
    parse_value=lambda v: DiagramID(str(v)) if v else None,
)

ExecutionIDScalar = strawberry.scalar(
    ExecutionID,
    name="ExecutionID",
    description="Unique identifier for executions",
    serialize=lambda v: str(v),
    parse_value=lambda v: ExecutionID(str(v)) if v else None,
)

HookIDScalar = strawberry.scalar(
    HookID,
    name="HookID",
    description="Unique identifier for hooks",
    serialize=lambda v: str(v),
    parse_value=lambda v: HookID(str(v)) if v else None,
)

TaskIDScalar = strawberry.scalar(
    TaskID,
    name="TaskID",
    description="Unique identifier for tasks",
    serialize=lambda v: str(v),
    parse_value=lambda v: TaskID(str(v)) if v else None,
)

# Export scalars
__all__ = [
    'NodeIDScalar',
    'HandleIDScalar',
    'ArrowIDScalar',
    'PersonIDScalar',
    'ApiKeyIDScalar',
    'DiagramIDScalar',
    'ExecutionIDScalar',
    'HookIDScalar',
    'TaskIDScalar',
]