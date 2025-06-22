from typing import List, Optional, NewType
from datetime import datetime

import strawberry
from strawberry.scalars import JSON

# Import domain models directly
from dipeo_domain import (
    DiagramMetadata,
    DomainApiKey,
    DomainArrow,
    DomainDiagram,
    DomainHandle,
    DomainNode,
    DomainPerson,
    ExecutionEvent,
    ExecutionState,
    NodeOutput,
    NodeState,
    TokenUsage,
    Vec2,
    ExecutionStatus,
    NodeType,
    LLMService,
    ForgettingMode,
    HandleDirection,
    DataType,
    DiagramFormat,
)


# SCALAR TYPES - Keep these as they provide GraphQL-specific type safety


NodeID = strawberry.scalar(
    NewType("NodeID", str),
    description="Unique identifier for a node",
    serialize=lambda v: str(v),
    parse_value=lambda v: str(v) if v else None,
)

DiagramID = strawberry.scalar(
    NewType("DiagramID", str),
    description="Unique identifier for a diagram",
    serialize=lambda v: str(v),
    parse_value=lambda v: str(v) if v else None,
)

ExecutionID = strawberry.scalar(
    NewType("ExecutionID", str),
    description="Unique identifier for an execution",
    serialize=lambda v: str(v),
    parse_value=lambda v: str(v) if v else None,
)

PersonID = strawberry.scalar(
    NewType("PersonID", str),
    description="Unique identifier for a person",
    serialize=lambda v: str(v),
    parse_value=lambda v: str(v) if v else None,
)

ApiKeyID = strawberry.scalar(
    NewType("ApiKeyID", str),
    description="Unique identifier for an API key",
    serialize=lambda v: str(v),
    parse_value=lambda v: str(v) if v else None,
)

HandleID = strawberry.scalar(
    NewType("HandleID", str),
    description="Unique identifier for a handle",
    serialize=lambda v: str(v),
    parse_value=lambda v: str(v) if v else None,
)

ArrowID = strawberry.scalar(
    NewType("ArrowID", str),
    description="Unique identifier for an arrow",
    serialize=lambda v: str(v),
    parse_value=lambda v: str(v) if v else None,
)

JSONScalar = strawberry.scalar(
    JSON,
    description="Arbitrary JSON data",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)

# SIMPLE TYPES - Direct conversions without custom fields


Vec2Type = strawberry.experimental.pydantic.type(Vec2, all_fields=True)
TokenUsageType = strawberry.experimental.pydantic.type(TokenUsage, all_fields=True)
NodeStateType = strawberry.experimental.pydantic.type(NodeState, all_fields=True)
NodeOutputType = strawberry.experimental.pydantic.type(NodeOutput, all_fields=True)
DomainHandleType = strawberry.experimental.pydantic.type(DomainHandle, all_fields=True)
DiagramMetadataType = strawberry.experimental.pydantic.type(DiagramMetadata, all_fields=True)

# TYPES WITH MINIMAL CUSTOM FIELDS

@strawberry.experimental.pydantic.type(DomainNode, all_fields=True)
class DomainNodeType:

    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        return getattr(self, '_data', None) or getattr(self, 'data', None)


@strawberry.experimental.pydantic.type(DomainArrow, all_fields=True)
class DomainArrowType:

    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        return getattr(self, '_data', None) or getattr(self, 'data', None)


@strawberry.experimental.pydantic.type(DomainPerson, all_fields=True)
class DomainPersonType:

    @strawberry.field
    def masked_api_key(self) -> Optional[str]:
        api_key_id = getattr(self, 'api_key_id', None)
        if not api_key_id:
            return None
        return f"****{str(api_key_id)[-4:]}"


@strawberry.experimental.pydantic.type(DomainApiKey, all_fields=True)
class DomainApiKeyType:

    @strawberry.field
    def masked_key(self) -> str:
        service = getattr(self, 'service', 'unknown')
        service_str = service.value if hasattr(service, 'value') else str(service)
        return f"{service_str}-****"


@strawberry.experimental.pydantic.type(DomainDiagram, all_fields=True)
class DomainDiagramType:
    pass  # Count fields can be computed in resolvers if needed


@strawberry.experimental.pydantic.type(ExecutionState, all_fields=True)
class ExecutionStateType:

    @strawberry.field
    def node_states(self) -> JSONScalar:
        return getattr(self, 'node_states', {})
    
    @strawberry.field
    def node_outputs(self) -> JSONScalar:
        return getattr(self, 'node_outputs', {})
    
    @strawberry.field
    def variables(self) -> JSONScalar:
        return getattr(self, 'variables', {})


@strawberry.experimental.pydantic.type(ExecutionEvent, all_fields=True)
class ExecutionEventType:
    """Execution event with JSON data field."""
    
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        return getattr(self, '_data', None) or getattr(self, 'data', None)


# INPUT TYPES - Create directly from what's needed

@strawberry.input
class Vec2Input:
    x: float
    y: float


@strawberry.input
class CreateNodeInput:
    type: NodeType
    position: Vec2Input
    label: str
    properties: Optional[JSONScalar] = None


@strawberry.input
class UpdateNodeInput:
    id: NodeID
    position: Optional[Vec2Input] = None
    label: Optional[str] = None
    properties: Optional[JSONScalar] = None


@strawberry.input
class CreateDiagramInput:
    name: str
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = strawberry.field(default_factory=list)


@strawberry.input
class CreatePersonInput:
    label: str
    service: LLMService
    model: str
    api_key_id: ApiKeyID
    system_prompt: Optional[str] = None
    forgetting_mode: ForgettingMode = ForgettingMode.no_forget
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None


@strawberry.input
class UpdatePersonInput:
    id: PersonID
    label: Optional[str] = None
    model: Optional[str] = None
    api_key_id: Optional[ApiKeyID] = None
    system_prompt: Optional[str] = None
    forgetting_mode: Optional[ForgettingMode] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None


@strawberry.input
class CreateApiKeyInput:
    label: str
    service: LLMService
    key: str


@strawberry.input
class ExecuteDiagramInput:
    diagram_id: Optional[DiagramID] = None
    diagram_data: Optional[JSONScalar] = None
    variables: Optional[JSONScalar] = None
    debug_mode: bool = False
    max_iterations: int = 100
    timeout_seconds: Optional[int] = None


@strawberry.input
class ExecutionControlInput:
    execution_id: ExecutionID
    action: str  # pause, resume, abort, skip_node
    node_id: Optional[NodeID] = None


@strawberry.input
class InteractiveResponseInput:
    execution_id: ExecutionID
    node_id: NodeID
    response: str


@strawberry.input
class CreateArrowInput:
    source: str  # format: "nodeId:handleId"
    target: str  # format: "nodeId:handleId"
    label: Optional[str] = None


@strawberry.input
class CreateHandleInput:
    node_id: NodeID
    label: str
    direction: HandleDirection
    data_type: DataType
    position: Vec2Input


@strawberry.input
class FileUploadInput:
    filename: str
    content_base64: str
    content_type: Optional[str] = None


@strawberry.input
class DiagramFilterInput:
    name_contains: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    modified_after: Optional[datetime] = None


@strawberry.input
class ExecutionFilterInput:
    diagram_id: Optional[DiagramID] = None
    status: Optional[ExecutionStatus] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    active_only: bool = False


# RESULT TYPES - Standardized mutation results

@strawberry.type
class MutationResult:
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class DiagramResult(MutationResult):
    diagram: Optional[DomainDiagramType] = None


@strawberry.type
class NodeResult(MutationResult):
    node: Optional[DomainNodeType] = None


@strawberry.type
class PersonResult(MutationResult):
    person: Optional[DomainPersonType] = None


@strawberry.type
class ApiKeyResult(MutationResult):
    api_key: Optional[DomainApiKeyType] = None


@strawberry.type
class TestApiKeyResult(MutationResult):
    valid: Optional[bool] = None
    available_models: Optional[List[str]] = None


@strawberry.type
class ExecutionResult(MutationResult):
    execution: Optional[ExecutionStateType] = None
    execution_id: Optional[str] = None


@strawberry.type
class DeleteResult(MutationResult):
    deleted_count: int = 0
    deleted_id: Optional[str] = None


@strawberry.type
class HandleResult(MutationResult):
    handle: Optional[DomainHandleType] = None


@strawberry.type
class ArrowResult(MutationResult):
    arrow: Optional[DomainArrowType] = None


@strawberry.type
class FileUploadResult(MutationResult):
    path: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None


@strawberry.type
class DiagramFormatInfo:
    id: str
    name: str
    description: str
    extension: str
    supports_import: bool
    supports_export: bool



# EXPORTS - What other modules should import

__all__ = [
    # Scalar types
    'NodeID', 'DiagramID', 'ExecutionID', 'PersonID', 'ApiKeyID', 'HandleID', 'ArrowID', 'JSONScalar',
    # Domain types
    'Vec2Type', 'TokenUsageType', 'NodeStateType', 'NodeOutputType', 'DomainHandleType',
    'DiagramMetadataType', 'DomainNodeType', 'DomainArrowType', 'DomainPersonType',
    'DomainApiKeyType', 'DomainDiagramType', 'ExecutionStateType', 'ExecutionEventType',
    # Input types
    'Vec2Input', 'CreateNodeInput', 'UpdateNodeInput', 'CreateDiagramInput',
    'CreatePersonInput', 'UpdatePersonInput', 'CreateApiKeyInput', 'ExecuteDiagramInput',
    'ExecutionControlInput', 'InteractiveResponseInput', 'CreateArrowInput',
    'CreateHandleInput', 'FileUploadInput', 'DiagramFilterInput', 'ExecutionFilterInput',
    # Result types
    'MutationResult', 'DiagramResult', 'NodeResult', 'PersonResult', 'ApiKeyResult',
    'TestApiKeyResult', 'ExecutionResult', 'DeleteResult', 'HandleResult', 'ArrowResult', 
    'FileUploadResult', 'DiagramFormatInfo',
    # Domain enums (re-exported for convenience)
    'NodeType', 'LLMService', 'ForgettingMode', 'HandleDirection', 'DataType',
    'ExecutionStatus', 'DiagramFormat',
]