from datetime import datetime
from typing import List, NewType, Optional

import strawberry

# Import domain models from the generated package
from dipeo_domain import (
    DataType,
    DiagramFormat,
    DiagramMetadata,
    DomainApiKey,
    DomainArrow,
    DomainDiagram,
    DomainHandle,
    DomainNode,
    DomainPerson,
    EventType,
    ExecutionEvent,
    ExecutionState,
    ExecutionStatus,
    ForgettingMode,
    HandleDirection,
    LLMService,
    NodeExecutionStatus,
    NodeOutput,
    NodeState,
    NodeType,
    TokenUsage,
    Vec2,
)

# SCALAR TYPES - Keep these for GraphQL-specific type safety
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

# Convert Pydantic models to Strawberry types
# This approach uses Strawberry's experimental Pydantic integration

# First, we need to register enums
NodeTypeEnum = strawberry.enum(NodeType)
HandleDirectionEnum = strawberry.enum(HandleDirection)
DataTypeEnum = strawberry.enum(DataType)
LLMServiceEnum = strawberry.enum(LLMService)
ForgettingModeEnum = strawberry.enum(ForgettingMode)
DiagramFormatEnum = strawberry.enum(DiagramFormat)
ExecutionStatusEnum = strawberry.enum(ExecutionStatus)
NodeExecutionStatusEnum = strawberry.enum(NodeExecutionStatus)
EventTypeEnum = strawberry.enum(EventType)


# Simple types - Direct conversions
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


# Types with custom fields
@strawberry.experimental.pydantic.type(
    DomainNode, fields=["id", "type", "position", "display_name"]
)
class DomainNodeType:
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        # Try multiple ways to access the data
        if hasattr(self, "_pydantic_object") and self._pydantic_object:
            return self._pydantic_object.data
        if hasattr(self, "data") and self.data is not None:
            return self.data
        if hasattr(self, "__strawberry_definition__"):
            # Try to access through the Strawberry definition
            origin = getattr(self, "__strawberry_definition__", {}).get("origin")
            if origin and hasattr(origin, "data"):
                return origin.data
        return None

    @strawberry.field
    def handles(self) -> List[DomainHandleType]:
        # Handles are resolved at the diagram level
        return []


@strawberry.experimental.pydantic.type(DomainArrow, fields=["id", "source", "target"])
class DomainArrowType:
    data: Optional[JSONScalar] = strawberry.auto


@strawberry.experimental.pydantic.type(
    DomainPerson,
    fields=["id", "label", "service", "model", "api_key_id", "system_prompt"],
)
class DomainPersonType:
    @strawberry.field
    def type(self) -> str:
        return "person"

    @strawberry.field
    def masked_api_key(self) -> Optional[str]:
        if hasattr(self, "_pydantic_object") and self._pydantic_object.api_key_id:
            return f"****{str(self._pydantic_object.api_key_id)[-4:]}"
        return None


@strawberry.experimental.pydantic.type(DomainApiKey, all_fields=True)
class DomainApiKeyType:
    @strawberry.field
    def masked_key(self) -> str:
        if hasattr(self, "_pydantic_object"):
            service = self._pydantic_object.service
            service_str = service.value if hasattr(service, "value") else str(service)
            return f"{service_str}-****"
        return "unknown-****"


@strawberry.experimental.pydantic.type(DomainDiagram, all_fields=True)
class DomainDiagramType:
    @strawberry.field
    def nodeCount(self) -> int:
        if hasattr(self, "_pydantic_object"):
            return len(self._pydantic_object.nodes)
        return 0

    @strawberry.field
    def arrowCount(self) -> int:
        if hasattr(self, "_pydantic_object"):
            return len(self._pydantic_object.arrows)
        return 0

    @strawberry.field
    def personCount(self) -> int:
        if hasattr(self, "_pydantic_object"):
            return len(self._pydantic_object.persons)
        return 0


@strawberry.experimental.pydantic.type(
    ExecutionState,
    fields=[
        "id",
        "status",
        "diagram_id",
        "started_at",
        "ended_at",
        "token_usage",
        "error",
        "duration_seconds",
        "is_active",
    ],
)
class ExecutionStateType:
    @strawberry.field
    def node_states(self) -> JSONScalar:
        if hasattr(self, "_pydantic_object") and self._pydantic_object.node_states:
            return {
                node_id: state.model_dump() if hasattr(state, "model_dump") else state
                for node_id, state in self._pydantic_object.node_states.items()
            }
        return {}

    @strawberry.field
    def node_outputs(self) -> JSONScalar:
        if hasattr(self, "_pydantic_object") and self._pydantic_object.node_outputs:
            result = {}
            for node_id, output in self._pydantic_object.node_outputs.items():
                if output is None:
                    result[node_id] = None
                elif hasattr(output, "model_dump"):
                    result[node_id] = output.model_dump()
                else:
                    result[node_id] = output
            return result
        return {}

    @strawberry.field
    def variables(self) -> JSONScalar:
        if hasattr(self, "_pydantic_object"):
            return self._pydantic_object.variables
        return {}


@strawberry.experimental.pydantic.type(
    ExecutionEvent,
    fields=[
        "execution_id",
        "sequence",
        "event_type",
        "node_id",
        "timestamp",
        "formatted_message",
    ],
)
class ExecutionEventType:
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        if hasattr(self, "_pydantic_object"):
            return self._pydantic_object.data
        return None


# INPUT TYPES - Create input types that match the domain model structure
@strawberry.input
class Vec2Input:
    x: float
    y: float


@strawberry.input
class CreateNodeInput:
    type: NodeTypeEnum
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
    service: LLMServiceEnum
    model: str
    api_key_id: ApiKeyID
    system_prompt: Optional[str] = None
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
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None


@strawberry.input
class CreateApiKeyInput:
    label: str
    service: LLMServiceEnum
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
    direction: HandleDirectionEnum
    data_type: DataTypeEnum
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
    status: Optional[ExecutionStatusEnum] = None
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


# Export all types
__all__ = [
    # Scalar types
    "NodeID",
    "DiagramID",
    "ExecutionID",
    "PersonID",
    "ApiKeyID",
    "HandleID",
    "ArrowID",
    "JSONScalar",
    # Domain types
    "Vec2Type",
    "TokenUsageType",
    "NodeStateType",
    "NodeOutputType",
    "DomainHandleType",
    "DiagramMetadataType",
    "DomainNodeType",
    "DomainArrowType",
    "DomainPersonType",
    "DomainApiKeyType",
    "DomainDiagramType",
    "ExecutionStateType",
    "ExecutionEventType",
    # Input types
    "Vec2Input",
    "CreateNodeInput",
    "UpdateNodeInput",
    "CreateDiagramInput",
    "CreatePersonInput",
    "UpdatePersonInput",
    "CreateApiKeyInput",
    "ExecuteDiagramInput",
    "ExecutionControlInput",
    "InteractiveResponseInput",
    "CreateArrowInput",
    "CreateHandleInput",
    "FileUploadInput",
    "DiagramFilterInput",
    "ExecutionFilterInput",
    # Result types
    "MutationResult",
    "DiagramResult",
    "NodeResult",
    "PersonResult",
    "ApiKeyResult",
    "TestApiKeyResult",
    "ExecutionResult",
    "DeleteResult",
    "HandleResult",
    "ArrowResult",
    "FileUploadResult",
    "DiagramFormatInfo",
    # Enums (re-exported for convenience)
    "NodeTypeEnum",
    "LLMServiceEnum",
    "ForgettingModeEnum",
    "HandleDirectionEnum",
    "DataTypeEnum",
    "ExecutionStatusEnum",
    "DiagramFormatEnum",
    "EventTypeEnum",
    "NodeExecutionStatusEnum",
]
