"""
Strawberry GraphQL domain types for DiPeO.
Auto-generated from TypeScript interfaces using simplified type resolver.

Generated at: 2025-09-21T20:14:14.580250
"""

import strawberry
from typing import Optional, Dict, Any, List, Union
from strawberry.scalars import JSON as JSONScalar

# Import the Pydantic domain models
from dipeo.diagram_generated.domain_models import (
    ClaudeCodeSession,
    SessionEvent,
    ClaudeCodeMessage,
    SessionMetadata,
    ToolUse,
    ToolResult,
    ConversationTurn,
    ClaudeCodeDiagramMetadata,
    SessionStatistics,
    SessionConversionOptions,
    WatchOptions,
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

# Import scalar types from shared file
from .scalar_aliases import (
    CliSessionIDScalar,
    NodeIDScalar,
    ArrowIDScalar,
    HandleIDScalar,
    PersonIDScalar,
    ApiKeyIDScalar,
    DiagramIDScalar,
    ExecutionIDScalar,
    FileIDScalar,
    HookIDScalar,
    TaskIDScalar,
    SerializedNodeOutput,
)

# Import generated types that already exist
from dipeo.diagram_generated.graphql.strawberry_domain import (
    ToolConfigType,
)

# Create Strawberry types from Pydantic models
# Order matters - define types that are referenced by others first

@strawberry.type
class ClaudeCodeSessionType:
    sessionId: str
    events: List[SessionEvent]
    metadata: SessionMetadata


@strawberry.type
class SessionEventType:
    type: str
    uuid: str
    parentUuid: Optional[str] = None
    timestamp: str
    message: ClaudeCodeMessage
    toolUse: Optional[ToolUse] = None
    toolResult: Optional[ToolResult] = None


@strawberry.type
class ClaudeCodeMessageType:
    role: str
    content: str


@strawberry.type
class SessionMetadataType:
    startTime: str
    endTime: Optional[str] = None
    totalEvents: float
    toolUsageCount: JSONScalar
    projectPath: Optional[str] = None


@strawberry.type
class ToolUseType:
    name: str
    input: JSONScalar


@strawberry.type
class ToolResultType:
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class ConversationTurnType:
    userEvent: SessionEvent
    assistantEvent: SessionEvent
    toolEvents: List[SessionEvent]


@strawberry.type
class ClaudeCodeDiagramMetadataType:
    sessionId: str
    createdAt: str
    eventCount: float
    nodeCount: float
    toolUsage: JSONScalar


@strawberry.type
class SessionStatisticsType:
    sessionId: str
    totalEvents: float
    userPrompts: float
    assistantResponses: float
    totalToolCalls: float
    toolBreakdown: JSONScalar
    duration: Optional[float] = None
    filesModified: List[str]
    commandsExecuted: List[str]


@strawberry.type
class SessionConversionOptionsType:
    outputDir: Optional[str] = None
    format: Optional[str] = None
    autoExecute: Optional[bool] = None
    mergeReads: Optional[bool] = None
    simplify: Optional[bool] = None
    preserveThinking: Optional[bool] = None


@strawberry.type
class WatchOptionsType:
    interval: Optional[float] = None
    autoConvert: Optional[bool] = None
    notifyOnNew: Optional[bool] = None


@strawberry.type
class CliSessionType:
    id: CliSessionIDScalar
    session_id: str
    user_id: Optional[str] = None
    started_at: str
    status: str
    metadata: Optional[JSONScalar] = None
    environment: Optional[JSONScalar] = None

    @staticmethod
    def from_pydantic(obj: CliSession) -> "CliSessionType":
        """Convert from Pydantic model"""
        return CliSessionType(
            id=obj.id,
            session_id=obj.session_id,
            user_id=obj.user_id,
            started_at=obj.started_at,
            status=str(obj.status.value) if hasattr(obj.status, 'value') else str(obj.status),
            metadata=obj.metadata,
            environment=obj.environment,
        )


@strawberry.type
class MessageType:
    id: Optional[str] = None
    from_person_id: str
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


@strawberry.experimental.pydantic.type(model=ConversationMetadata, all_fields=True)
class ConversationMetadataType:
    """Auto-generated from Pydantic model"""
    pass


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


@strawberry.experimental.pydantic.type(model=Vec2, all_fields=True)
class Vec2Type:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=DomainHandle, all_fields=True)
class DomainHandleType:
    """Auto-generated from Pydantic model"""
    pass


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
            execution_priority=obj.execution_priority,
            data=obj.data,
        )


@strawberry.experimental.pydantic.type(model=PersonLLMConfig, all_fields=True)
class PersonLLMConfigType:
    """Auto-generated from Pydantic model"""
    pass


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


@strawberry.experimental.pydantic.type(model=DomainApiKey, all_fields=True)
class DomainApiKeyType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=DiagramMetadata, all_fields=True)
class DiagramMetadataType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.type
class DomainDiagramType:
    nodes: List[DomainNodeType]
    handles: List[DomainHandleType]
    arrows: List[DomainArrowType]
    persons: List[DomainPersonType]
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


@strawberry.experimental.pydantic.type(model=LLMUsage, all_fields=True)
class LLMUsageType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=NodeState, all_fields=True)
class NodeStateType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=NodeMetrics, all_fields=True)
class NodeMetricsType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=Bottleneck, all_fields=True)
class BottleneckType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.type
class ExecutionMetricsType:
    execution_id: ExecutionIDScalar
    start_time: float
    end_time: Optional[float] = None
    total_duration_ms: Optional[float] = None
    node_metrics: JSONScalar
    critical_path: Optional[List[str]] = None
    parallelizable_groups: Optional[List[List[str]]] = None
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


@strawberry.experimental.pydantic.type(model=EnvelopeMeta, all_fields=True)
class EnvelopeMetaType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=SerializedEnvelope, all_fields=True)
class SerializedEnvelopeType:
    """Auto-generated from Pydantic model"""
    pass


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
    is_active: Optional[bool] = None
    exec_counts: JSONScalar
    executed_nodes: List[str]
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


@strawberry.experimental.pydantic.type(model=InteractivePromptData, all_fields=True)
class InteractivePromptDataType:
    """Auto-generated from Pydantic model"""
    pass


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


@strawberry.experimental.pydantic.type(model=NodeDefinition, all_fields=True)
class NodeDefinitionType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=File, all_fields=True)
class FileType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=ToolConfig, all_fields=True)
class ToolConfigType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=WebSearchResult, all_fields=True)
class WebSearchResultType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=ImageGenerationResult, all_fields=True)
class ImageGenerationResultType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=ToolOutput, all_fields=True)
class ToolOutputType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=LLMRequestOptions, all_fields=True)
class LLMRequestOptionsType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=NodeUpdate, all_fields=True)
class NodeUpdateType:
    """Auto-generated from Pydantic model"""
    pass


@strawberry.experimental.pydantic.type(model=InteractivePrompt, all_fields=True)
class InteractivePromptType:
    """Auto-generated from Pydantic model"""
    pass


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


@strawberry.experimental.pydantic.type(model=KeepalivePayload, all_fields=True)
class KeepalivePayloadType:
    """Auto-generated from Pydantic model"""
    pass


