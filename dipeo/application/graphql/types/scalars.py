"""
Strawberry scalar types for DiPeO IDs.

This module extends the generated scalars with additional ID types not yet
included in code generation (HookID and TaskID).
"""

import strawberry
from strawberry.scalars import JSON

from dipeo.diagram_generated.domain_models import HookID, TaskID

# Re-export all generated scalars
from dipeo.diagram_generated.graphql.scalars import *

# Register additional ID types not in generated scalars
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

# Alias for backward compatibility
JSONScalar = JSON

# Export all scalars (generated + additional)
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
