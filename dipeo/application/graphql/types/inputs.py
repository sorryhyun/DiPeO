"""GraphQL input types for DiPeO mutations."""

import strawberry
from typing import Optional, List
from datetime import datetime

from strawberry.scalars import JSON as JSONScalar

# Import scalars to ensure they're registered
from .scalars import (
    NodeIDScalar, ArrowIDScalar, HandleIDScalar, PersonIDScalar,
    ApiKeyIDScalar, DiagramIDScalar, ExecutionIDScalar
)

# Import enums from generated modules
from dipeo.diagram_generated.enums import (
    NodeType, ExecutionStatus, NodeExecutionStatus,
    LLMService, APIServiceType
)
# Import DiagramFormat with proper GraphQL mapping
from dipeo.application.graphql.enums import DiagramFormat


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
    position: Optional[Vec2Input] = None
    data: Optional[strawberry.scalars.JSON] = None


@strawberry.input
class CreateArrowInput:
    source: strawberry.ID
    target: strawberry.ID
    label: Optional[str] = None
    data: Optional[strawberry.scalars.JSON] = None


@strawberry.input
class CreateDiagramInput:
    name: str
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = strawberry.field(default_factory=list)


@strawberry.input
class UpdateDiagramInput:
    name: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None


@strawberry.input
class PersonLLMConfigInput:
    service: LLMService
    model: str
    api_key_id: strawberry.ID
    system_prompt: Optional[str] = None


@strawberry.input
class CreatePersonInput:
    label: str
    llm_config: PersonLLMConfigInput
    type: str = "user"


@strawberry.input
class UpdatePersonInput:
    label: Optional[str] = None
    llm_config: Optional[PersonLLMConfigInput] = None


@strawberry.input
class CreateApiKeyInput:
    label: str
    service: APIServiceType
    key: str


@strawberry.input
class ExecuteDiagramInput:
    diagram_id: Optional[strawberry.ID] = None
    diagram_data: Optional[strawberry.scalars.JSON] = None
    variables: Optional[strawberry.scalars.JSON] = None
    debug_mode: Optional[bool] = None
    max_iterations: Optional[int] = None
    timeout_seconds: Optional[int] = None
    use_unified_monitoring: Optional[bool] = None


@strawberry.input
class FileOperationInput:
    diagram_id: strawberry.ID
    format: DiagramFormat


@strawberry.input
class UpdateNodeStateInput:
    execution_id: strawberry.ID
    node_id: strawberry.ID
    status: NodeExecutionStatus
    output: Optional[strawberry.scalars.JSON] = None
    error: Optional[str] = None


@strawberry.input
class DiagramFilterInput:
    name: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@strawberry.input
class ExecutionFilterInput:
    diagram_id: Optional[strawberry.ID] = None
    status: Optional[ExecutionStatus] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None


@strawberry.input
class ExecutionControlInput:
    execution_id: strawberry.ID
    action: str  # "pause", "resume", "cancel"
    reason: Optional[str] = None


@strawberry.input
class InteractiveResponseInput:
    execution_id: strawberry.ID
    node_id: strawberry.ID
    response: str
    metadata: Optional[strawberry.scalars.JSON] = None


@strawberry.input
class RegisterCliSessionInput:
    execution_id: str
    diagram_name: str
    diagram_format: str
    diagram_data: Optional[strawberry.scalars.JSON] = None


@strawberry.input
class UnregisterCliSessionInput:
    execution_id: str