from typing import List, Optional, NewType, Dict, Any
from datetime import datetime

import strawberry

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
    EventType,
    NodeExecutionStatus,
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
    NewType("JSONScalar", object),
    name="JSONScalar",
    description="Arbitrary JSON data",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)

# SIMPLE TYPES - Direct conversions without custom fields

# Register Vec2 type explicitly to ensure it's available for nested usage
@strawberry.experimental.pydantic.type(Vec2, all_fields=True)
class Vec2Type:
    pass
@strawberry.experimental.pydantic.type(TokenUsage, all_fields=True)
class TokenUsageType:
    pass
@strawberry.experimental.pydantic.type(NodeState, all_fields=True)
class NodeStateType:
    pass
@strawberry.experimental.pydantic.type(NodeOutput, all_fields=True)
class NodeOutputType:
    pass
@strawberry.experimental.pydantic.type(DomainHandle, all_fields=True)
class DomainHandleType:
    pass
@strawberry.experimental.pydantic.type(DiagramMetadata, all_fields=True)
class DiagramMetadataType:
    pass

# TYPES WITH MINIMAL CUSTOM FIELDS

@strawberry.experimental.pydantic.type(DomainNode, fields=["id", "type", "position", "display_name"])
class DomainNodeType:
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        return getattr(self, '_data', None) or getattr(self, 'data', None)
    
    @strawberry.field
    def handles(self) -> List[DomainHandleType]:
        # Handles are stored at the diagram level, need to be resolved via parent
        # For now, return empty list - actual resolution happens in resolver
        return []


@strawberry.experimental.pydantic.type(DomainArrow, fields=["id", "source", "target"])
class DomainArrowType:
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        return getattr(self, '_data', None) or getattr(self, 'data', None)


@strawberry.experimental.pydantic.type(DomainPerson, fields=["id", "label", "service", "model", "api_key_id", "system_prompt", "forgetting_mode"])
class DomainPersonType:
    @strawberry.field
    def type(self) -> str:
        return "person"
    
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
    @strawberry.field
    def nodeCount(self) -> int:
        nodes = getattr(self, 'nodes', [])
        return len(nodes) if nodes else 0
    
    @strawberry.field
    def arrowCount(self) -> int:
        arrows = getattr(self, 'arrows', [])
        return len(arrows) if arrows else 0
    
    @strawberry.field
    def personCount(self) -> int:
        persons = getattr(self, 'persons', [])
        return len(persons) if persons else 0


@strawberry.experimental.pydantic.type(ExecutionState, fields=["id", "status", "diagram_id", "started_at", "ended_at", "token_usage", "error", "duration_seconds", "is_active"])
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


@strawberry.experimental.pydantic.type(ExecutionEvent, fields=["execution_id", "sequence", "event_type", "node_id", "timestamp", "formatted_message"])
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