"""Strawberry scalar types for DiPeO IDs."""

import strawberry
from strawberry.scalars import JSON

from dipeo.diagram_generated.domain_models import HookID, TaskID
from dipeo.diagram_generated.graphql.scalars import *

HookIDScalar = strawberry.scalar(
    HookID,
    name="HookID",
    description="Unique identifier for hooks",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: HookID(v) if v is not None else None,
)

TaskIDScalar = strawberry.scalar(
    TaskID,
    name="TaskID",
    description="Unique identifier for tasks",
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: TaskID(v) if v is not None else None,
)

JSONScalar = JSON
__all__ = [
    # From generated
    "ApiKeyIDScalar",
    "ArrowIDScalar",
    "DiagramIDScalar",
    "ExecutionIDScalar",
    "HandleIDScalar",
    # Additional
    "HookIDScalar",
    "JSONScalar",
    "NodeIDScalar",
    "PersonIDScalar",
    "TaskIDScalar",
]
