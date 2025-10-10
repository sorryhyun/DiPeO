"""
Strawberry GraphQL domain types for DiPeO.
Auto-generated from TypeScript interfaces using simplified type resolver.

Generated at: 2025-10-10T14:03:06.740326
"""

from __future__ import annotations

import strawberry
from typing import Optional, Dict, Any, List, Union, Literal, TypeAlias, TYPE_CHECKING
from strawberry.scalars import JSON
from .inputs import Float, String, Boolean
from dipeo.domain.type_defs import JsonValue, JsonDict

# Type aliases for Strawberry
# JSON from strawberry.scalars is used directly for runtime
# For type checking, we treat it as Any since it's a ScalarWrapper
if TYPE_CHECKING:
    JSONScalar = Any
else:
    JSONScalar = JSON

DefaultValue: TypeAlias = Union[str, float, bool, None, Dict[str, Any], List[Any]]
ValidationSeverity: TypeAlias = Literal["error", "warning"]

# Import the Pydantic domain models
from ..domain_models import (
    PersonID, PersonLLMConfig, DiagramID, ToolResult,
    ExecutionState, NodeState, ParseResult, LLMUsage
)

# Import required enums for GraphQL type resolution
from ..enums import (
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
    QueryOperationType,
    CrudOperation,
    QueryEntity,
    FieldPreset,
    FieldGroup,
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
class AuthConfigType:
    """AuthConfig domain type"""
    strategy: str
    header: Optional[str] = None
    query_param: Optional[str] = None
    format: Optional[str] = None
    scopes: Optional[List[str]] = None


@strawberry.type
class BatchInputType:
    """BatchInput domain type"""
    sources: JSONScalar


@strawberry.type
class BatchResultType:
    """BatchResult domain type"""
    results: Dict[str, ParseResult]
    metadata: Optional[JSONScalar] = None


@strawberry.type
class BottleneckType:
    """Bottleneck domain type"""
    node_id: str
    node_type: str
    duration_ms: float
    percentage: float


@strawberry.type
class ClaudeCodeDiagramMetadataType:
    """ClaudeCodeDiagramMetadata domain type"""
    sessionId: str
    createdAt: str
    eventCount: float
    nodeCount: float
    toolUsage: JSONScalar


@strawberry.type
class ClaudeCodeMessageType:
    """ClaudeCodeMessage domain type"""
    role: str
    content: str


@strawberry.type
class CliSessionType:
    """CliSession domain type"""
    id: CliSessionIDScalar
    session_id: str
    user_id: Optional[str] = None
    started_at: str
    status: str
    metadata: Optional[JSONScalar] = None
    environment: Optional[JSONScalar] = None


@strawberry.type
class CliSessionResultType:
    """CliSessionResult domain type"""
    success: bool
    session: Optional[CliSessionType] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class ConstantInfoType:
    """ConstantInfo domain type"""
    name: str
    type: str
    value: JSONScalar
    isExported: bool
    jsDoc: Optional[str] = None


@strawberry.type
class ConversationMetadataType:
    """ConversationMetadata domain type"""
    started_at: str
    total_tokens: float
    message_count: float


@strawberry.type
class DefaultValueConfigType:
    """DefaultValueConfig domain type"""
    tsValue: DefaultValue
    pyValue: Optional[str] = None
    gqlValue: Optional[JSONScalar] = None
    description: Optional[str] = None


@strawberry.type
class DiagramMetadataType:
    """DiagramMetadata domain type"""
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    version: str
    created: str
    modified: str
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    format: Optional[str] = None


@strawberry.type
class DiffPatchInputType:
    """DiffPatchInput domain type"""
    filePath: str
    oldContent: Optional[str] = None
    newContent: Optional[str] = None
    patch: Optional[str] = None


@strawberry.type
class DomainApiKeyType:
    """DomainApiKey domain type"""
    id: ApiKeyIDScalar
    label: str
    service: APIServiceType
    key: Optional[str] = None


@strawberry.type
class DomainArrowType:
    """DomainArrow domain type"""
    id: ArrowIDScalar
    source: HandleIDScalar
    target: HandleIDScalar
    content_type: Optional[ContentType] = None
    label: Optional[str] = None
    execution_priority: Optional[float] = None
    data: Optional[JSONScalar] = None


@strawberry.type
class DomainHandleType:
    """DomainHandle domain type"""
    id: HandleIDScalar
    node_id: NodeIDScalar
    label: HandleLabel
    direction: HandleDirection
    data_type: DataType
    position: Optional[str] = None


@strawberry.type
class EnumMemberType:
    """EnumMember domain type"""
    name: str
    value: Optional[JSONScalar] = None


@strawberry.type
class EnumInfoType:
    """EnumInfo domain type"""
    name: str
    members: List[EnumMemberType]
    isExported: bool
    jsDoc: Optional[str] = None


@strawberry.type
class ExecutionLogEntryType:
    """ExecutionLogEntry domain type"""
    execution_id: ExecutionIDScalar
    node_id: Optional[NodeIDScalar] = None
    level: str
    message: str
    context: Optional[JSONScalar] = None
    timestamp: str


@strawberry.type
class ExecutionMetricsType:
    """ExecutionMetrics domain type"""
    execution_id: ExecutionIDScalar
    start_time: float
    end_time: Optional[float] = None
    total_duration_ms: Optional[float] = None
    node_metrics: JSONScalar
    critical_path: Optional[List[str]] = None
    parallelizable_groups: Optional[List[List[str]]] = None
    bottlenecks: Optional[List[BottleneckType]] = None


@strawberry.type
class ExecutionOptionsType:
    """ExecutionOptions domain type"""
    mode: Optional[str] = None
    timeout: Optional[float] = None
    variables: Optional[JSONScalar] = None
    debug: Optional[bool] = None


@strawberry.type
class ExecutionUpdateType:
    """ExecutionUpdate domain type"""
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


@strawberry.type
class FileType:
    """File domain type"""
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
class FileOperationResultType:
    """FileOperationResult domain type"""
    success: bool
    file: Optional[FileType] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class ImageGenerationResultType:
    """ImageGenerationResult domain type"""
    image_data: str
    format: str
    width: Optional[float] = None
    height: Optional[float] = None


@strawberry.type
class IntegrationTestResultType:
    """IntegrationTestResult domain type"""
    success: bool
    provider: str
    operation: str
    status_code: Optional[float] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    response_preview: Optional[JSONScalar] = None


@strawberry.type
class InteractivePromptType:
    """InteractivePrompt domain type"""
    execution_id: ExecutionIDScalar
    node_id: NodeIDScalar
    prompt: str
    timeout: Optional[float] = None
    default_value: Optional[str] = None
    options: Optional[List[str]] = None
    timestamp: str


@strawberry.type
class InteractivePromptDataType:
    """InteractivePromptData domain type"""
    node_id: NodeIDScalar
    prompt: str
    timeout: Optional[float] = None
    default_value: Optional[str] = None


@strawberry.type
class InteractiveResponseType:
    """InteractiveResponse domain type"""
    node_id: NodeIDScalar
    response: str
    timestamp: str


@strawberry.type
class KeepalivePayloadType:
    """KeepalivePayload domain type"""
    type: str
    timestamp: str


@strawberry.type
class LLMUsageType:
    """LLMUsage domain type"""
    input: float
    output: float
    cached: Optional[float] = None
    total: Optional[float] = None

    @staticmethod
    def from_pydantic(obj: LLMUsage) -> "LLMUsageType":
        """Convert from Pydantic model"""
        return LLMUsageType(
            input=obj.input,
            output=obj.output,
            cached=obj.cached,
            total=obj.total,
        )


@strawberry.type
class EnvelopeMetaType:
    """EnvelopeMeta domain type"""
    node_id: Optional[str] = None
    llm_usage: Optional[LLMUsageType] = None
    execution_time: Optional[float] = None
    retry_count: Optional[float] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: Optional[JSONScalar] = None


@strawberry.type
class MessageType:
    """Message domain type"""
    id: Optional[str] = None
    from_person_id: str
    to_person_id: PersonIDScalar
    content: str
    timestamp: Optional[str] = None
    token_count: Optional[float] = None
    message_type: str
    metadata: Optional[JSONScalar] = None


@strawberry.type
class ConversationType:
    """Conversation domain type"""
    messages: List[MessageType]
    metadata: Optional[ConversationMetadataType] = None


@strawberry.type
class NodeDefinitionType:
    """NodeDefinition domain type"""
    type: str
    handler: JSONScalar
    requires_services: Optional[List[str]] = None
    description: Optional[str] = None


@strawberry.type
class NodeMetricsType:
    """NodeMetrics domain type"""
    node_id: str
    node_type: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    memory_usage: Optional[float] = None
    llm_usage: Optional[LLMUsageType] = None
    error: Optional[str] = None
    dependencies: Optional[List[str]] = None
    module_timings: Optional[JSONScalar] = None


@strawberry.type
class NodeUpdateType:
    """NodeUpdate domain type"""
    execution_id: ExecutionIDScalar
    node_id: NodeIDScalar
    status: Status
    progress: Optional[float] = None
    output: Optional[JSONScalar] = None
    error: Optional[str] = None
    metrics: Optional[JSONScalar] = None
    timestamp: str


@strawberry.type
class OperationType:
    """Operation domain type"""
    name: str
    method: str
    path: str
    description: Optional[str] = None
    required_scopes: Optional[List[str]] = None
    has_pagination: bool
    timeout_override: Optional[float] = None


@strawberry.type
class OperationSchemaType:
    """OperationSchema domain type"""
    operation: str
    method: str
    path: str
    description: Optional[str] = None
    request_body: Optional[JSONScalar] = None
    query_params: Optional[JSONScalar] = None
    response: Optional[JSONScalar] = None


@strawberry.type
class ParameterInfoType:
    """ParameterInfo domain type"""
    name: str
    type: str
    optional: bool
    defaultValue: Optional[str] = None


@strawberry.type
class FunctionInfoType:
    """FunctionInfo domain type"""
    name: str
    parameters: List[ParameterInfoType]
    returnType: str
    isAsync: bool
    isExported: bool
    jsDoc: Optional[str] = None


@strawberry.type
class MethodInfoType:
    """MethodInfo domain type"""
    name: str
    parameters: List[ParameterInfoType]
    returnType: str
    isAsync: bool
    jsDoc: Optional[str] = None


@strawberry.type
class PersonLLMConfigType:
    """PersonLLMConfig domain type"""
    service: LLMService
    model: str
    api_key_id: ApiKeyIDScalar
    system_prompt: Optional[str] = None
    prompt_file: Optional[str] = None


@strawberry.type
class DomainPersonType:
    """DomainPerson domain type"""
    id: PersonIDScalar
    label: str
    llm_config: PersonLLMConfigType
    type: str


@strawberry.type
class PropertyInfoType:
    """PropertyInfo domain type"""
    name: str
    type: str
    optional: bool
    readonly: bool
    jsDoc: Optional[str] = None


@strawberry.type
class ClassInfoType:
    """ClassInfo domain type"""
    name: str
    properties: List[PropertyInfoType]
    methods: List[MethodInfoType]
    extends: Optional[str] = None
    implements: Optional[List[str]] = None
    isExported: bool
    jsDoc: Optional[str] = None


@strawberry.type
class InterfaceInfoType:
    """InterfaceInfo domain type"""
    name: str
    properties: List[PropertyInfoType]
    extends: Optional[List[str]] = None
    isExported: bool
    jsDoc: Optional[str] = None


@strawberry.type
class ProviderMetadataType:
    """ProviderMetadata domain type"""
    version: str
    type: str
    manifest_path: Optional[str] = None
    description: Optional[str] = None
    documentation_url: Optional[str] = None
    support_email: Optional[str] = None


@strawberry.type
class ProviderStatisticsType:
    """ProviderStatistics domain type"""
    total_providers: float
    total_operations: float
    provider_types: JSONScalar
    providers: JSONScalar


@strawberry.type
class QueryFieldType:
    """QueryField domain type"""
    name: str
    required: Optional[bool] = None
    fields: Optional[List[QueryFieldType]] = None


@strawberry.type
class EntityQueryConfigType:
    """EntityQueryConfig domain type"""
    entity: str
    operations: List[CrudOperation]
    defaultFields: List[QueryFieldType]
    relationships: Optional[JSONScalar] = None


@strawberry.type
class QueryManifestType:
    """QueryManifest domain type"""
    version: str
    entities: List[EntityQueryConfigType]


@strawberry.type
class QueryVariableType:
    """QueryVariable domain type"""
    name: str
    type: str
    required: bool


@strawberry.type
class QuerySpecificationType:
    """QuerySpecification domain type"""
    name: str
    operation: QueryOperationType
    entityType: str
    description: Optional[str] = None
    variables: Optional[List[QueryVariableType]] = None
    returnType: str
    fields: List[QueryFieldType]
    template: Optional[str] = None


@strawberry.type
class RateLimitConfigType:
    """RateLimitConfig domain type"""
    algorithm: str
    capacity: float
    refill_per_sec: float
    window_size_sec: Optional[float] = None


@strawberry.type
class RelationshipConfigType:
    """RelationshipConfig domain type"""
    field: str
    type: str
    targetEntity: str
    includeByDefault: Optional[bool] = None
    defaultFields: Optional[List[str]] = None


@strawberry.type
class RetryPolicyType:
    """RetryPolicy domain type"""
    strategy: str
    max_retries: float
    base_delay_ms: float
    max_delay_ms: Optional[float] = None
    retry_on_status: List[float]


@strawberry.type
class ProviderType:
    """Provider domain type"""
    name: str
    operations: List[OperationType]
    metadata: ProviderMetadataType
    base_url: Optional[str] = None
    auth_config: Optional[AuthConfigType] = None
    rate_limit: Optional[RateLimitConfigType] = None
    retry_policy: Optional[RetryPolicyType] = None
    default_timeout: float


@strawberry.type
class SerializedEnvelopeType:
    """SerializedEnvelope domain type"""
    envelope_format: str
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
class SessionConversionOptionsType:
    """SessionConversionOptions domain type"""
    outputDir: Optional[str] = None
    format: Optional[str] = None
    autoExecute: Optional[bool] = None
    mergeReads: Optional[bool] = None
    simplify: Optional[bool] = None
    preserveThinking: Optional[bool] = None


@strawberry.type
class SessionMetadataType:
    """SessionMetadata domain type"""
    startTime: str
    endTime: Optional[str] = None
    totalEvents: float
    toolUsageCount: JSONScalar
    projectPath: Optional[str] = None


@strawberry.type
class SessionStatisticsType:
    """SessionStatistics domain type"""
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
class ToolConfigType:
    """ToolConfig domain type"""
    type: ToolType
    enabled: Optional[bool] = None
    config: Optional[JSONScalar] = None


@strawberry.type
class LLMRequestOptionsType:
    """LLMRequestOptions domain type"""
    temperature: Optional[float] = None
    max_tokens: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[float] = None
    tools: Optional[List[ToolConfigType]] = None
    response_format: Optional[JSONScalar] = None


@strawberry.type
class ToolOutputType:
    """ToolOutput domain type"""
    type: ToolType
    result: JSONScalar
    raw_response: Optional[JSONScalar] = None


@strawberry.type
class ChatResultType:
    """ChatResult domain type"""
    text: str
    llm_usage: Optional[LLMUsageType] = None
    raw_response: Optional[JSONScalar] = None
    tool_outputs: Optional[List[ToolOutputType]] = None


@strawberry.type
class ToolResultType:
    """ToolResult domain type"""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class ToolUseType:
    """ToolUse domain type"""
    name: str
    input: JSONScalar


@strawberry.type
class SessionEventType:
    """SessionEvent domain type"""
    type: str
    uuid: str
    parentUuid: Optional[str] = None
    timestamp: str
    message: ClaudeCodeMessageType
    toolUse: Optional[ToolUseType] = None
    toolResult: Optional[ToolResultType] = None


@strawberry.type
class ClaudeCodeSessionType:
    """ClaudeCodeSession domain type"""
    sessionId: str
    events: List[SessionEventType]
    metadata: SessionMetadataType


@strawberry.type
class ConversationTurnType:
    """ConversationTurn domain type"""
    userEvent: SessionEventType
    assistantEvent: SessionEventType
    toolEvents: List[SessionEventType]


@strawberry.type
class TypeAliasInfoType:
    """TypeAliasInfo domain type"""
    name: str
    type: str
    isExported: bool
    jsDoc: Optional[str] = None


@strawberry.type
class ParseResultType:
    """ParseResult domain type"""
    ast: JSONScalar
    interfaces: List[InterfaceInfoType]
    types: List[TypeAliasInfoType]
    enums: List[EnumInfoType]
    classes: Optional[List[ClassInfoType]] = None
    functions: Optional[List[FunctionInfoType]] = None
    constants: Optional[List[ConstantInfoType]] = None
    error: Optional[str] = None


@strawberry.type
class ValidationErrorType:
    """ValidationError domain type"""
    field: str
    message: str
    severity: ValidationSeverity
    code: Optional[str] = None


@strawberry.type
class ValidationResultType:
    """ValidationResult domain type"""
    valid: bool
    errors: List[ValidationErrorType]
    warnings: List[ValidationErrorType]


@strawberry.type
class Vec2Type:
    """Vec2 domain type"""
    x: float
    y: float


@strawberry.type
class DomainNodeType:
    """DomainNode domain type"""
    id: NodeIDScalar
    type: NodeType
    position: Vec2Type
    data: JSONScalar


@strawberry.type
class DomainDiagramType:
    """DomainDiagram domain type"""
    nodes: List[DomainNodeType]
    handles: List[DomainHandleType]
    arrows: List[DomainArrowType]
    persons: List[DomainPersonType]
    metadata: Optional[DiagramMetadataType] = None


@strawberry.type
class WatchOptionsType:
    """WatchOptions domain type"""
    interval: Optional[float] = None
    autoConvert: Optional[bool] = None
    notifyOnNew: Optional[bool] = None


@strawberry.type
class WebSearchResultType:
    """WebSearchResult domain type"""
    url: str
    title: str
    snippet: str
    score: Optional[float] = None



# Special cases for ExecutionState and NodeState
@strawberry.type
class NodeStateType:
    """NodeState domain type"""
    status: Status
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    error: Optional[str] = None
    llm_usage: Optional[LLMUsageType] = None
    output: Optional[JSONScalar] = None

    @staticmethod
    def from_pydantic(obj: NodeState) -> "NodeStateType":
        """Convert from Pydantic model"""
        return NodeStateType(
            status=obj.status,
            started_at=obj.started_at,
            ended_at=obj.ended_at,
            error=obj.error,
            llm_usage=LLMUsageType.from_pydantic(obj.llm_usage) if obj.llm_usage else None,
            output=obj.output,
        )

@strawberry.type
class ExecutionStateType:
    """ExecutionState domain type"""
    id: ExecutionIDScalar
    status: Status
    diagram_id: Optional[DiagramIDScalar] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    error: Optional[str] = None
    llm_usage: Optional[LLMUsageType] = None
    is_active: Optional[bool] = None
    executed_nodes: List[str]
    node_states: JSONScalar
    node_outputs: JSONScalar
    variables: Optional[JSONScalar] = None
    exec_counts: JSONScalar
    metrics: Optional[JSONScalar] = None

    @staticmethod
    def from_pydantic(obj: ExecutionState) -> "ExecutionStateType":
        """Convert from Pydantic model"""
        return ExecutionStateType(
            id=obj.id,
            status=obj.status,
            diagram_id=obj.diagram_id,
            started_at=obj.started_at,
            ended_at=obj.ended_at,
            error=obj.error,
            llm_usage=LLMUsageType.from_pydantic(obj.llm_usage) if obj.llm_usage else None,
            is_active=obj.is_active,
            executed_nodes=obj.executed_nodes,
            node_states={k: v.model_dump() for k, v in obj.node_states.items()},
            node_outputs={k: v.model_dump() for k, v in obj.node_outputs.items()},
            variables=obj.variables,
            exec_counts=obj.exec_counts,
            metrics=obj.metrics,
        )
