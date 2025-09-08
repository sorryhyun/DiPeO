"""
GraphQL input types for DiPeO mutations.
Auto-generated from TypeScript definitions.

Generated at: 2025-09-08T16:41:30.566024
"""

from datetime import datetime
from typing import Optional

import strawberry


# Import enums from generated modules
from dipeo.diagram_generated.enums import APIServiceType, LLMService, NodeType, Status, DiagramFormat

# Import scalars to ensure they're registered
from dipeo.diagram_generated.graphql.scalars import *



@strawberry.input
class Vec2Input:
    x: float
    y: float


@strawberry.input
class CreateNodeInput:
    type: NodeType
    position: Vec2Input
    data: strawberry.scalars.JSON


@strawberry.input
class UpdateNodeInput:
    position: Vec2Input | None = None
    data: strawberry.scalars.JSON | None = None


@strawberry.input
class CreateArrowInput:
    source: strawberry.ID
    target: strawberry.ID
    label: str | None = None
    data: strawberry.scalars.JSON | None = None


@strawberry.input
class CreateDiagramInput:
    name: str
    description: str | None = None
    author: str | None = None
    tags: list[str] = strawberry.field(default_factory=list)


@strawberry.input
class UpdateDiagramInput:
    name: str | None = None
    description: str | None = None
    author: str | None = None
    tags: list[str] | None = None


@strawberry.input
class PersonLLMConfigInput:
    service: LLMService
    model: str
    api_key_id: strawberry.ID
    system_prompt: str | None = None


@strawberry.input
class CreatePersonInput:
    label: str
    llm_config: PersonLLMConfigInput
    type: str = "user"


@strawberry.input
class UpdatePersonInput:
    label: str | None = None
    llm_config: PersonLLMConfigInput | None = None


@strawberry.input
class CreateApiKeyInput:
    label: str
    service: APIServiceType
    key: str


@strawberry.input
class ExecuteDiagramInput:
    diagram_id: strawberry.ID | None = None
    diagram_data: strawberry.scalars.JSON | None = None
    variables: strawberry.scalars.JSON | None = None
    debug_mode: bool | None = None
    max_iterations: int | None = None
    timeout_seconds: int | None = None
    use_unified_monitoring: bool | None = None


@strawberry.input
class FileOperationInput:
    diagram_id: strawberry.ID
    format: DiagramFormat


@strawberry.input
class UpdateNodeStateInput:
    execution_id: strawberry.ID
    node_id: strawberry.ID
    status: Status
    output: strawberry.scalars.JSON | None = None
    error: str | None = None


@strawberry.input
class DiagramFilterInput:
    name: str | None = None
    author: str | None = None
    tags: list[str] | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


@strawberry.input
class ExecutionFilterInput:
    diagram_id: strawberry.ID | None = None
    status: Status | None = None
    started_after: datetime | None = None
    started_before: datetime | None = None


@strawberry.input
class ExecutionControlInput:
    execution_id: strawberry.ID
    action: str
    reason: str | None = None


@strawberry.input
class InteractiveResponseInput:
    execution_id: strawberry.ID
    node_id: strawberry.ID
    response: str
    metadata: strawberry.scalars.JSON | None = None


@strawberry.input
class RegisterCliSessionInput:
    execution_id: str
    diagram_name: str
    diagram_format: str
    diagram_data: strawberry.scalars.JSON | None = None
    diagram_path: str | None = None


@strawberry.input
class UnregisterCliSessionInput:
    execution_id: str


# Export all input types
__all__ = [
    'Vec2Input',
    'CreateNodeInput',
    'UpdateNodeInput',
    'CreateArrowInput',
    'CreateDiagramInput',
    'UpdateDiagramInput',
    'PersonLLMConfigInput',
    'CreatePersonInput',
    'UpdatePersonInput',
    'CreateApiKeyInput',
    'ExecuteDiagramInput',
    'FileOperationInput',
    'UpdateNodeStateInput',
    'DiagramFilterInput',
    'ExecutionFilterInput',
    'ExecutionControlInput',
    'InteractiveResponseInput',
    'RegisterCliSessionInput',
    'UnregisterCliSessionInput',
]
