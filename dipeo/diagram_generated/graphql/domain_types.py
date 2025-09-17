"""
Strawberry GraphQL domain types for DiPeO.
Auto-generated from TypeScript interfaces using simplified type resolver.

Generated at: 2025-09-17T19:31:22.449458
"""

import strawberry
from typing import Optional, Dict, Any, List, Union
from strawberry.scalars import JSON as JSONScalar

# Import the Pydantic domain models
from dipeo.diagram_generated.domain_models import (
    CliSession,
    Message,
    ConversationMetadata,
    Conversation,
    Vec2,
    DomainHandle,
    DomainNode,
    DomainArrow,
    PersonLLMConfig,
    DomainPerson,
    DomainApiKey,
    DiagramMetadata,
    DomainDiagram,
    LLMUsage,
    NodeState,
    NodeMetrics,
    Bottleneck,
    ExecutionMetrics,
    EnvelopeMeta,
    SerializedEnvelope,
    ExecutionState,
    ExecutionOptions,
    InteractivePromptData,
    ExecutionUpdate,
    NodeDefinition,
    File,
    ToolConfig,
    WebSearchResult,
    ImageGenerationResult,
    ToolOutput,
    LLMRequestOptions,
    NodeUpdate,
    InteractivePrompt,
    ExecutionLogEntry,
    KeepalivePayload,
)

# Import required enums for GraphQL type resolution
from dipeo.diagram_generated.enums import (
    Status,
    NodeType,
    EventType,
    HandleLabel,
    HandleDirection,
    DataType,
    ContentType,
    LLMService,
    APIServiceType,
    ToolType,
)

# Import scalar types
from .scalars import (
    CliSessionIDScalar,
    NodeIDScalar,
    ArrowIDScalar,
    HandleIDScalar,
    PersonIDScalar,
    ApiKeyIDScalar,
    DiagramIDScalar,
    HookIDScalar,
    TaskIDScalar,
    ExecutionIDScalar,
    FileIDScalar,
)

# Note: HookIDScalar and TaskIDScalar are not branded types yet
# TODO: Add these as branded types in TypeScript models
from strawberry.scalars import ID
HookIDScalar = ID  # Temporary fallback
TaskIDScalar = ID  # Temporary fallback

# Define undefined types
SerializedNodeOutput = JSONScalar  # Temporary - this type is not defined in TypeScript

# Import generated types that already exist
from dipeo.diagram_generated.graphql.strawberry_domain import (
    ToolConfigType,
)

# Create Strawberry types from Pydantic models
# Order matters - define types that are referenced by others first

@strawberry.type
class CliSessionType:
    id: CliSessionIDScalar
    session_id: str
    user_id: Optional[str] = None
    started_at: str
    last_active: Optional[str] = None
    status: str
    metadata: Optional[JSONScalar] = None
    current_directory: Optional[str] = None
    environment: Optional[JSONScalar] = None

    @staticmethod
    def from_pydantic(obj: CliSession) -> "CliSessionType":
        """Convert from Pydantic model"""
        return CliSessionType(
            id=obj.id,
            session_id=obj.session_id,
            user_id=obj.user_id,
            started_at=obj.started_at,
            last_active=obj.last_active,
            status=str(obj.status.value) if hasattr(obj.status, 'value') else str(obj.status),
            metadata=obj.metadata,
            current_directory=obj.current_directory,
            environment=obj.environment,
        )


@strawberry.type
class MessageType:
    id: Optional[str] = None
    from_person_id: JSONScalar
    to_person_id: PersonIDScalar
    content: str
    timestamp: Optional[str] = None
    token_count: Optional[float] = None
    message_type: str
    metadata: Optional[JSONScalar] = None

    @staticmethod
    def from_pydantic(obj: Message) -> "MessageType":
        """Convert from Pydantic model"""
        return MessageType(
            id=obj.id,
            from_person_id=obj.from_person_id,
            to_person_id=obj.to_person_id,
            content=obj.content,
            timestamp=obj.timestamp,
            token_count=obj.token_count,
            message_type=obj.message_type,
            metadata=obj.metadata,
        )


@strawberry.type
class ConversationMetadataType:
    started_at: str
    last_message_at: str
    total_tokens: float
    message_count: float
    context_resets: float


@strawberry.type
class ConversationType:
    messages: List[MessageType]
    metadata: Optional[ConversationMetadataType] = None

    @staticmethod
    def from_pydantic(obj: Conversation) -> "ConversationType":
        """Convert from Pydantic model"""
        return ConversationType(
            messages=obj.messages,
            metadata=obj.metadata,
        )


@strawberry.type
class Vec2Type:
    x: float
    y: float


@strawberry.type
class DomainHandleType:
    id: HandleIDScalar
    node_id: NodeIDScalar
    label: HandleLabel
    direction: HandleDirection
    data_type: DataType
    position: Optional[str] = None


@strawberry.type
class DomainNodeType:
    id: NodeIDScalar
    type: NodeType
    position: Vec2Type
    data: JSONScalar

    @staticmethod
    def from_pydantic(obj: DomainNode) -> "DomainNodeType":
        """Convert from Pydantic model"""
        # Convert position
        position = Vec2Type.from_pydantic(obj.position) if hasattr(Vec2Type, 'from_pydantic') else Vec2Type(x=obj.position.x, y=obj.position.y)
        return DomainNodeType(
            id=obj.id,
            type=str(obj.type.value) if hasattr(obj.type, 'value') else str(obj.type),
            position=obj.position,
            data=obj.data,
        )


@strawberry.type
class DomainArrowType:
    id: ArrowIDScalar
    source: HandleIDScalar
    target: HandleIDScalar
    content_type: Optional[ContentType] = None
    label: Optional[str] = None
    packing: Optional[str] = None
    execution_priority: Optional[float] = None
    data: Optional[JSONScalar] = None

    @staticmethod
    def from_pydantic(obj: DomainArrow) -> "DomainArrowType":
        """Convert from Pydantic model"""
        return DomainArrowType(
            id=obj.id,
            source=obj.source,
            target=obj.target,
            content_type=str(obj.content_type.value) if hasattr(obj.content_type, 'value') else str(obj.content_type),
            label=obj.label,
            packing=obj.packing,
            execution_priority=obj.execution_priority,
            data=obj.data,
        )


@strawberry.type
class PersonLLMConfigType:
    service: LLMService
    model: str
    api_key_id: ApiKeyIDScalar
    system_prompt: Optional[str] = None
    prompt_file: Optional[str] = None


@strawberry.type
class DomainPersonType:
    id: PersonIDScalar
    label: str
    llm_config: PersonLLMConfigType
    type: str

    @staticmethod
    def from_pydantic(obj: DomainPerson) -> "DomainPersonType":
        """Convert from Pydantic model"""
        return DomainPersonType(
            id=obj.id,
            label=obj.label,
            llm_config=obj.llm_config,
            type=str(obj.type.value) if hasattr(obj.type, 'value') else str(obj.type),
        )


@strawberry.type
class DomainApiKeyType:
    id: ApiKeyIDScalar
    label: str
    service: APIServiceType
    key: Optional[str] = None


@strawberry.type
class DiagramMetadataType:
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    version: str
    created: str
    modified: str
    author: Optional[str] = None
    tags: Optional[list[str]] = None
    format: Optional[str] = None


@strawberry.type
class DomainDiagramType:
    nodes: list[DomainNodeType]
    handles: list[DomainHandleType]
    arrows: list[DomainArrowType]
    persons: list[DomainPersonType]
    metadata: Optional[DiagramMetadataType] = None

    @staticmethod
    def from_pydantic(obj: DomainDiagram) -> "DomainDiagramType":
        """Convert from Pydantic model"""
        return DomainDiagramType(
            nodes=[DomainNodeType.from_pydantic(item) for item in obj.nodes] if obj.nodes else [],
            handles=[DomainHandleType.from_pydantic(item) for item in obj.handles] if obj.handles else [],
            arrows=[DomainArrowType.from_pydantic(item) for item in obj.arrows] if obj.arrows else [],
            persons=[DomainPersonType.from_pydantic(item) for item in obj.persons] if obj.persons else [],
            metadata=obj.metadata,
        )


@strawberry.type
class LLMUsageType:
    input: float
    output: float
    cached: Optional[float] = None
    total: Optional[float] = None


@strawberry.type
class NodeStateType:
    status: Status
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    error: Optional[str] = None
    llm_usage: Optional[LLMUsageType] = None
    output: Optional[JSONScalar] = None


@strawberry.type
class NodeMetricsType:
    node_id: str
    node_type: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    memory_usage: Optional[float] = None
    llm_usage: Optional[LLMUsageType] = None
    error: Optional[str] = None
    dependencies: Optional[list[str]] = None


@strawberry.type
class BottleneckType:
    node_id: str
    node_type: str
    duration_ms: float
    percentage: float


@strawberry.type
class ExecutionMetricsType:
    execution_id: ExecutionIDScalar
    start_time: float
    end_time: Optional[float] = None
    total_duration_ms: Optional[float] = None
    node_metrics: JSONScalar
    critical_path: Optional[list[str]] = None
    parallelizable_groups: Optional[list[List[str]]] = None
    bottlenecks: Optional[List[BottleneckType]] = None

    @staticmethod
    def from_pydantic(obj: ExecutionMetrics) -> "ExecutionMetricsType":
        """Convert from Pydantic model"""
        return ExecutionMetricsType(
            execution_id=obj.execution_id,
            start_time=obj.start_time,
            end_time=obj.end_time,
            total_duration_ms=obj.total_duration_ms,
            node_metrics={k: v.model_dump() if hasattr(v, 'model_dump') else v
                        for k, v in obj.node_metrics.items()} if obj.node_metrics else {},
            critical_path=obj.critical_path,
            parallelizable_groups=obj.parallelizable_groups,
            bottlenecks=obj.bottlenecks,
        )


@strawberry.type
class EnvelopeMetaType:
    node_id: Optional[str] = None
    llm_usage: Optional[LLMUsageType] = None
    execution_time: Optional[float] = None
    retry_count: Optional[float] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: Optional[JSONScalar] = None


@strawberry.type
class SerializedEnvelopeType:
    envelope_format: bool = True
    id: str
    trace_id: str
    produced_by: str
    content_type: str
    schema_id: Optional[str] = None
    serialization_format: Optional[str] = None
    body: JSONScalar
    meta: EnvelopeMetaType
    representations: Optional[JSONScalar] = None


@strawberry.type
class ExecutionStateType:
    id: str
    status: Status
    diagram_id: Optional[DiagramIDScalar] = None
    started_at: str
    ended_at: Optional[str] = None
    node_states: JSONScalar
    node_outputs: JSONScalar
    llm_usage: LLMUsageType
    error: Optional[str] = None
    variables: Optional[JSONScalar] = None
    metadata: Optional[JSONScalar] = None
    duration_seconds: Optional[float] = None
    is_active: Optional[bool] = None
    exec_counts: JSONScalar
    executed_nodes: list[str]
    metrics: Optional[ExecutionMetricsType] = None

    @staticmethod
    def from_pydantic(obj: ExecutionState) -> "ExecutionStateType":
        """Convert from Pydantic model"""
        # Convert nested types
        llm_usage = LLMUsageType.from_pydantic(obj.llm_usage) if hasattr(LLMUsageType, 'from_pydantic') else obj.llm_usage
        metrics = ExecutionMetricsType.from_pydantic(obj.metrics) if obj.metrics and hasattr(ExecutionMetricsType, 'from_pydantic') else obj.metrics
        return ExecutionStateType(
            id=obj.id,
            status=str(obj.status.value) if hasattr(obj.status, 'value') else str(obj.status),
            diagram_id=obj.diagram_id,
            started_at=obj.started_at,
            ended_at=obj.ended_at,
            node_states={k: v.model_dump() if hasattr(v, 'model_dump') else v
                        for k, v in obj.node_states.items()} if obj.node_states else {},
            node_outputs={k: v.model_dump() if hasattr(v, 'model_dump') else v
                        for k, v in obj.node_outputs.items()} if obj.node_outputs else {},
            llm_usage=obj.llm_usage,
            error=obj.error,
            variables=obj.variables,
            metadata=obj.metadata,
            duration_seconds=obj.duration_seconds,
            is_active=obj.is_active,
            exec_counts={k: v.model_dump() if hasattr(v, 'model_dump') else v
                        for k, v in obj.exec_counts.items()} if obj.exec_counts else {},
            executed_nodes=obj.executed_nodes,
            metrics=obj.metrics,
        )


@strawberry.type
class ExecutionOptionsType:
    mode: Optional[str] = None
    timeout: Optional[float] = None
    variables: Optional[JSONScalar] = None
    debug: Optional[bool] = None

    @staticmethod
    def from_pydantic(obj: ExecutionOptions) -> "ExecutionOptionsType":
        """Convert from Pydantic model"""
        return ExecutionOptionsType(
            mode=obj.mode,
            timeout=obj.timeout,
            variables=obj.variables,
            debug=obj.debug,
        )


@strawberry.type
class InteractivePromptDataType:
    node_id: NodeIDScalar
    prompt: str
    timeout: Optional[float] = None
    default_value: Optional[str] = None


@strawberry.type
class ExecutionUpdateType:
    type: EventType
    execution_id: ExecutionIDScalar
    node_id: Optional[NodeIDScalar] = None
    status: Optional[Status] = None
    result: Optional[JSONScalar] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None
    total_tokens: Optional[float] = None
    node_type: Optional[str] = None
    tokens: Optional[float] = None
    data: Optional[JSONScalar] = None

    @staticmethod
    def from_pydantic(obj: ExecutionUpdate) -> "ExecutionUpdateType":
        """Convert from Pydantic model"""
        return ExecutionUpdateType(
            type=str(obj.type.value) if hasattr(obj.type, 'value') else str(obj.type),
            execution_id=obj.execution_id,
            node_id=obj.node_id,
            status=str(obj.status.value) if hasattr(obj.status, 'value') else str(obj.status),
            result=obj.result,
            error=obj.error,
            timestamp=obj.timestamp,
            total_tokens=obj.total_tokens,
            node_type=obj.node_type,
            tokens=obj.tokens,
            data=obj.data,
        )


@strawberry.type
class NodeDefinitionType:
    type: str
    node_schema: JSONScalar
    handler: JSONScalar
    requires_services: Optional[list[str]] = None
    description: Optional[str] = None


@strawberry.type
class FileType:
    id: FileIDScalar
    name: str
    path: str
    content: Optional[str] = None
    size: Optional[float] = None
    mime_type: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    metadata: Optional[JSONScalar] = None


@strawberry.type
class ToolConfigType:
    type: ToolType
    enabled: Optional[bool] = None
    config: Optional[JSONScalar] = None


@strawberry.type
class WebSearchResultType:
    url: str
    title: str
    snippet: str
    score: Optional[float] = None


@strawberry.type
class ImageGenerationResultType:
    image_data: str
    format: str
    width: Optional[float] = None
    height: Optional[float] = None


@strawberry.type
class ToolOutputType:
    type: ToolType
    result: JSONScalar
    raw_response: Optional[JSONScalar] = None


@strawberry.type
class LLMRequestOptionsType:
    temperature: Optional[float] = None
    max_tokens: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[float] = None
    tools: Optional[list[ToolConfig]] = None
    response_format: Optional[JSONScalar] = None


@strawberry.type
class NodeUpdateType:
    execution_id: ExecutionIDScalar
    node_id: NodeIDScalar
    status: Status
    progress: Optional[float] = None
    output: Optional[JSONScalar] = None
    error: Optional[str] = None
    metrics: Optional[JSONScalar] = None
    timestamp: str


@strawberry.type
class InteractivePromptType:
    execution_id: ExecutionIDScalar
    node_id: NodeIDScalar
    prompt_id: str
    prompt: str
    timeout: Optional[float] = None
    default_value: Optional[str] = None
    options: Optional[list[str]] = None
    timestamp: str


@strawberry.type
class ExecutionLogEntryType:
    execution_id: ExecutionIDScalar
    node_id: Optional[NodeIDScalar] = None
    level: str
    message: str
    context: Optional[JSONScalar] = None
    timestamp: str

    @staticmethod
    def from_pydantic(obj: ExecutionLogEntry) -> "ExecutionLogEntryType":
        """Convert from Pydantic model"""
        return ExecutionLogEntryType(
            execution_id=obj.execution_id,
            node_id=obj.node_id,
            level=obj.level,
            message=obj.message,
            context=obj.context,
            timestamp=obj.timestamp,
        )


@strawberry.type
class KeepalivePayloadType:
    type: str
    timestamp: str

    @staticmethod
    def from_pydantic(obj: KeepalivePayload) -> "KeepalivePayloadType":
        """Convert from Pydantic model"""
        return KeepalivePayloadType(
            type=str(obj.type.value) if hasattr(obj.type, 'value') else str(obj.type),
            timestamp=obj.timestamp,
        )


