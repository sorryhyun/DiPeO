"""
Shared scalar type aliases for Strawberry GraphQL.
Auto-generated to avoid duplication across generated files.

Generated at: 2025-09-18T13:14:39.011793
"""

import strawberry
from strawberry.scalars import ID, JSON as JSONScalar

# Type aliases for ID scalars
# These are simple aliases to ID for now, but can be upgraded to branded types later
CliSessionIDScalar = ID
NodeIDScalar = ID
ArrowIDScalar = ID
HandleIDScalar = ID
PersonIDScalar = ID
ApiKeyIDScalar = ID
DiagramIDScalar = ID
ExecutionIDScalar = ID
FileIDScalar = ID
HookIDScalar = ID
TaskIDScalar = ID

# Temporary types that need proper definition in TypeScript models
SerializedNodeOutput = JSONScalar  # Placeholder for node output serialization

# Export all scalars
__all__ = [
    "CliSessionIDScalar",
    "NodeIDScalar",
    "ArrowIDScalar",
    "HandleIDScalar",
    "PersonIDScalar",
    "ApiKeyIDScalar",
    "DiagramIDScalar",
    "ExecutionIDScalar",
    "FileIDScalar",
    "HookIDScalar",
    "TaskIDScalar",
    "SerializedNodeOutput",
    "JSONScalar",
]
