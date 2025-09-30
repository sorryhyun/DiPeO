#!/usr/bin/env python3
# __generated__ by DiPeO
"""
Domain models generated from TypeScript interfaces.
Generated at: 2025-09-30T00:55:42.919644
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Any, Dict, List, Literal, NewType, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from dipeo.domain.type_defs import JsonDict, JsonList, JsonPrimitive, JsonValue

from .enums import *
from .integrations import *

# NewType declarations

CliSessionID = NewType('CliSessionID', str)

NodeID = NewType('NodeID', str)

ArrowID = NewType('ArrowID', str)

HandleID = NewType('HandleID', str)

PersonID = NewType('PersonID', str)

ApiKeyID = NewType('ApiKeyID', str)

DiagramID = NewType('DiagramID', str)

HookID = NewType('HookID', str)

TaskID = NewType('TaskID', str)

ExecutionID = NewType('ExecutionID', str)

FileID = NewType('FileID', str)



class CliSession(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: CliSessionID
    
    session_id: str
    
    user_id: str | None = Field(default=None)
    
    started_at: str
    
    status: Literal['active', 'inactive', 'terminated']
    
    metadata: Dict[str, Any] | None = Field(default=None)
    
    environment: Dict[str, str] | None = Field(default=None)
    



class CliSessionResult(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    success: bool
    
    session: CliSession | None = Field(default=None)
    
    message: str | None = Field(default=None)
    
    error: str | None = Field(default=None)
    



class Message(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: str | None = Field(default=None)
    
    from_person_id: Union[PersonID, Literal['system']]
    
    to_person_id: PersonID
    
    content: str
    
    timestamp: str | None = Field(default=None)
    
    token_count: float | None = Field(default=None)
    
    message_type: Literal['person_to_person', 'system_to_person', 'person_to_system']
    
    metadata: JsonDict | None = Field(default=None)
    



class ConversationMetadata(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    started_at: str
    
    total_tokens: float
    
    message_count: float
    



class Conversation(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    messages: List[Message]
    
    metadata: ConversationMetadata | None = Field(default=None)
    



class Vec2(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    x: float
    
    y: float
    



class DomainHandle(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: HandleID
    
    node_id: NodeID
    
    label: HandleLabel
    
    direction: HandleDirection
    
    data_type: DataType
    
    position: Optional[str] | None = Field(default=None)
    



class DomainNode(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: NodeID
    
    type: NodeType
    
    position: Vec2
    
    data: JsonDict
    



class DomainArrow(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: ArrowID
    
    source: HandleID
    
    target: HandleID
    
    content_type: Optional[ContentType] | None = Field(default=None)
    
    label: Optional[str] | None = Field(default=None)
    
    execution_priority: Optional[float] | None = Field(default=None)
    
    data: Optional[Dict[str, Any]] | None = Field(default=None)
    



class PersonLLMConfig(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    service: LLMService
    
    model: str
    
    api_key_id: ApiKeyID
    
    system_prompt: Optional[str] | None = Field(default=None)
    
    prompt_file: Optional[str] | None = Field(default=None)
    



class DomainPerson(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: PersonID
    
    label: str
    
    llm_config: PersonLLMConfig
    
    type: Literal['person']
    



class DomainApiKey(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: ApiKeyID
    
    label: str
    
    service: APIServiceType
    
    key: str | None = Field(default=None)
    



class DiagramMetadata(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: Optional[DiagramID] | None = Field(default=None)
    
    name: Optional[str] | None = Field(default=None)
    
    description: Optional[str] | None = Field(default=None)
    
    version: str
    
    created: str
    
    modified: str
    
    author: Optional[str] | None = Field(default=None)
    
    tags: Optional[List[str]] | None = Field(default=None)
    
    format: Optional[str] | None = Field(default=None)
    



class DomainDiagram(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    nodes: List[DomainNode]
    
    handles: List[DomainHandle]
    
    arrows: List[DomainArrow]
    
    persons: List[DomainPerson]
    
    metadata: Optional[DiagramMetadata] | None = Field(default=None)
    



class LLMUsage(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    input: float
    
    output: float
    
    cached: Optional[float] | None = Field(default=None)
    
    total: float | None = Field(default=None)
    



class NodeState(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    status: Status
    
    started_at: Optional[str] | None = Field(default=None)
    
    ended_at: Optional[str] | None = Field(default=None)
    
    error: Optional[str] | None = Field(default=None)
    
    llm_usage: Optional[LLMUsage] | None = Field(default=None)
    
    output: Optional[Dict[str, Any]] | None = Field(default=None)
    



class NodeMetrics(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    node_id: str
    
    node_type: str
    
    start_time: float
    
    end_time: Optional[float] | None = Field(default=None)
    
    duration_ms: Optional[float] | None = Field(default=None)
    
    memory_usage: Optional[float] | None = Field(default=None)
    
    llm_usage: Optional[LLMUsage] | None = Field(default=None)
    
    error: Optional[str] | None = Field(default=None)
    
    dependencies: List[str] | None = Field(default=None)
    



class Bottleneck(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    node_id: str
    
    node_type: str
    
    duration_ms: float
    
    percentage: float
    



class ExecutionMetrics(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    execution_id: ExecutionID
    
    start_time: float
    
    end_time: Optional[float] | None = Field(default=None)
    
    total_duration_ms: Optional[float] | None = Field(default=None)
    
    node_metrics: Dict[str, NodeMetrics]
    
    critical_path: List[str] | None = Field(default=None)
    
    parallelizable_groups: List[List[str]] | None = Field(default=None)
    
    bottlenecks: List[Bottleneck] | None = Field(default=None)
    



class EnvelopeMeta(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    node_id: str | None = Field(default=None)
    
    llm_usage: LLMUsage | None = Field(default=None)
    
    execution_time: float | None = Field(default=None)
    
    retry_count: float | None = Field(default=None)
    
    error: str | None = Field(default=None)
    
    error_type: str | None = Field(default=None)
    
    timestamp: Union[str, float] | None = Field(default=None)
    



class SerializedEnvelope(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    envelope_format: Literal[True]
    
    id: str
    
    trace_id: str
    
    produced_by: str
    
    content_type: str
    
    schema_id: str | None = Field(default=None)
    
    serialization_format: str | None = Field(default=None)
    
    body: Any
    
    meta: EnvelopeMeta
    
    representations: Dict[str, Any] | None = Field(default=None)
    



class ExecutionState(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: ExecutionID
    
    status: Status
    
    diagram_id: Optional[DiagramID] | None = Field(default=None)
    
    started_at: str
    
    ended_at: Optional[str] | None = Field(default=None)
    
    node_states: Dict[str, NodeState]
    
    node_outputs: Dict[str, SerializedEnvelope]
    
    llm_usage: LLMUsage
    
    error: Optional[str] | None = Field(default=None)
    
    variables: JsonDict | None = Field(default=None)
    
    metadata: JsonDict | None = Field(default=None)
    
    is_active: bool | None = Field(default=None)
    
    exec_counts: Dict[str, float]
    
    executed_nodes: List[str]
    
    metrics: Optional[ExecutionMetrics] | None = Field(default=None)
    



class ExecutionOptions(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    mode: Literal['normal', 'debug', 'monitor'] | None = Field(default=None)
    
    timeout: float | None = Field(default=None)
    
    variables: JsonDict | None = Field(default=None)
    
    debug: bool | None = Field(default=None)
    



class InteractivePromptData(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    node_id: NodeID
    
    prompt: str
    
    timeout: float | None = Field(default=None)
    
    default_value: Optional[str] | None = Field(default=None)
    



class InteractiveResponse(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    node_id: NodeID
    
    response: str
    
    timestamp: str
    



class ExecutionUpdate(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: EventType
    
    execution_id: ExecutionID
    
    node_id: NodeID | None = Field(default=None)
    
    status: Status | None = Field(default=None)
    
    result: JsonValue | None = Field(default=None)
    
    error: str | None = Field(default=None)
    
    timestamp: str | None = Field(default=None)
    
    total_tokens: float | None = Field(default=None)
    
    node_type: str | None = Field(default=None)
    
    tokens: float | None = Field(default=None)
    
    data: Dict[str, Any] | None = Field(default=None)
    



class NodeDefinition(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: str
    
    handler: Any
    
    requires_services: List[str] | None = Field(default=None)
    
    description: str | None = Field(default=None)
    



class File(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: FileID
    
    name: str
    
    path: str
    
    content: str | None = Field(default=None)
    
    size: float | None = Field(default=None)
    
    mime_type: str | None = Field(default=None)
    
    created_at: str | None = Field(default=None)
    
    modified_at: str | None = Field(default=None)
    
    metadata: Dict[str, Any] | None = Field(default=None)
    



class FileOperationResult(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    success: bool
    
    file: File | None = Field(default=None)
    
    message: str | None = Field(default=None)
    
    error: str | None = Field(default=None)
    



class ToolConfig(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: ToolType
    
    enabled: bool | None = Field(default=None)
    
    config: Dict[str, Any] | None = Field(default=None)
    



class WebSearchResult(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    url: str
    
    title: str
    
    snippet: str
    
    score: float | None = Field(default=None)
    



class ImageGenerationResult(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    image_data: str
    
    format: str
    
    width: float | None = Field(default=None)
    
    height: float | None = Field(default=None)
    



class ToolOutput(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: ToolType
    
    result: Union[List[WebSearchResult], ImageGenerationResult, Any]
    
    raw_response: Any | None = Field(default=None)
    



class ChatResult(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    text: str
    
    llm_usage: Optional[LLMUsage] | None = Field(default=None)
    
    raw_response: Optional[Any] | None = Field(default=None)
    
    tool_outputs: Optional[List[ToolOutput]] | None = Field(default=None)
    



class LLMRequestOptions(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    temperature: float | None = Field(default=None)
    
    max_tokens: float | None = Field(default=None)
    
    top_p: float | None = Field(default=None)
    
    n: float | None = Field(default=None)
    
    tools: List[ToolConfig] | None = Field(default=None)
    
    response_format: Any | None = Field(default=None)
    



class NodeUpdate(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    execution_id: ExecutionID
    
    node_id: NodeID
    
    status: Status
    
    progress: float | None = Field(default=None)
    
    output: Any | None = Field(default=None)
    
    error: str | None = Field(default=None)
    
    metrics: Dict[str, Any] | None = Field(default=None)
    
    timestamp: str
    



class InteractivePrompt(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    execution_id: ExecutionID
    
    node_id: NodeID
    
    prompt: str
    
    timeout: float | None = Field(default=None)
    
    default_value: Optional[str] | None = Field(default=None)
    
    options: List[str] | None = Field(default=None)
    
    timestamp: str
    



class ExecutionLogEntry(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    execution_id: ExecutionID
    
    node_id: NodeID | None = Field(default=None)
    
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    message: str
    
    context: Dict[str, Any] | None = Field(default=None)
    
    timestamp: str
    



class KeepalivePayload(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: Literal['keepalive']
    
    timestamp: str
    



class ParseResult(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    ast: Any
    
    interfaces: List[InterfaceInfo]
    
    types: List[TypeAliasInfo]
    
    enums: List[EnumInfo]
    
    classes: List[ClassInfo] | None = Field(default=None)
    
    functions: List[FunctionInfo] | None = Field(default=None)
    
    constants: List[ConstantInfo] | None = Field(default=None)
    
    error: str | None = Field(default=None)
    



class InterfaceInfo(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    properties: List[PropertyInfo]
    
    extends: List[str] | None = Field(default=None)
    
    isExported: bool
    
    jsDoc: str | None = Field(default=None)
    



class PropertyInfo(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    type: str
    
    optional: bool
    
    readonly: bool
    
    jsDoc: str | None = Field(default=None)
    



class TypeAliasInfo(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    type: str
    
    isExported: bool
    
    jsDoc: str | None = Field(default=None)
    



class EnumInfo(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    members: List[EnumMember]
    
    isExported: bool
    
    jsDoc: str | None = Field(default=None)
    



class EnumMember(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    value: Union[str, float] | None = Field(default=None)
    



class ClassInfo(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    properties: List[PropertyInfo]
    
    methods: List[MethodInfo]
    
    extends: str | None = Field(default=None)
    
    implements: List[str] | None = Field(default=None)
    
    isExported: bool
    
    jsDoc: str | None = Field(default=None)
    



class MethodInfo(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    parameters: List[ParameterInfo]
    
    returnType: str
    
    isAsync: bool
    
    jsDoc: str | None = Field(default=None)
    



class ParameterInfo(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    type: str
    
    optional: bool
    
    defaultValue: str | None = Field(default=None)
    



class FunctionInfo(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    parameters: List[ParameterInfo]
    
    returnType: str
    
    isAsync: bool
    
    isExported: bool
    
    jsDoc: str | None = Field(default=None)
    



class ConstantInfo(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    type: str
    
    value: Any
    
    isExported: bool
    
    jsDoc: str | None = Field(default=None)
    



class BatchInput(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    sources: Dict[str, str]
    



class BatchResult(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    results: Dict[str, ParseResult]
    
    metadata: Dict[str, Any] | None = Field(default=None)
    



class QueryField(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    required: bool | None = Field(default=None)
    
    fields: List[QueryField] | None = Field(default=None)
    



class QueryVariable(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    type: str
    
    required: bool
    



class QuerySpecification(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    operation: QueryOperationType
    
    entityType: str
    
    description: str | None = Field(default=None)
    
    variables: List[QueryVariable] | None = Field(default=None)
    
    returnType: str
    
    fields: List[QueryField]
    
    template: str | None = Field(default=None)
    



class EntityQueryConfig(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    entity: str
    
    operations: List[CrudOperation]
    
    defaultFields: List[QueryField]
    
    relationships: List[Dict[str, Any]] | None = Field(default=None)
    



class QueryManifest(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    version: str
    
    entities: List[EntityQueryConfig]
    



class RelationshipConfig(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    field: str
    
    type: Literal['one-to-one', 'one-to-many', 'many-to-many']
    
    targetEntity: str
    
    includeByDefault: bool | None = Field(default=None)
    
    defaultFields: List[str] | None = Field(default=None)
    



class ClaudeCodeSession(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    sessionId: str
    
    events: List[SessionEvent]
    
    metadata: SessionMetadata
    



class SessionEvent(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: Literal['user', 'assistant', 'summary']
    
    uuid: str
    
    parentUuid: str | None = Field(default=None)
    
    timestamp: str
    
    message: ClaudeCodeMessage
    
    toolUse: ToolUse | None = Field(default=None)
    
    toolResult: ToolResult | None = Field(default=None)
    



class ClaudeCodeMessage(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    role: Literal['user', 'assistant']
    
    content: str
    



class SessionMetadata(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    startTime: str
    
    endTime: str | None = Field(default=None)
    
    totalEvents: float
    
    toolUsageCount: Dict[str, float]
    
    projectPath: str | None = Field(default=None)
    



class ToolUse(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    input: Dict[str, Any]
    



class ToolResult(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    success: bool
    
    output: str | None = Field(default=None)
    
    error: str | None = Field(default=None)
    



class ConversationTurn(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    userEvent: SessionEvent
    
    assistantEvent: SessionEvent
    
    toolEvents: List[SessionEvent]
    



class DiffPatchInput(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    filePath: str
    
    oldContent: str | None = Field(default=None)
    
    newContent: str | None = Field(default=None)
    
    patch: str | None = Field(default=None)
    



class ClaudeCodeDiagramMetadata(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    sessionId: str
    
    createdAt: str
    
    eventCount: float
    
    nodeCount: float
    
    toolUsage: Dict[str, float]
    



class SessionStatistics(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    sessionId: str
    
    totalEvents: float
    
    userPrompts: float
    
    assistantResponses: float
    
    totalToolCalls: float
    
    toolBreakdown: Dict[str, float]
    
    duration: float | None = Field(default=None)
    
    filesModified: List[str]
    
    commandsExecuted: List[str]
    



class SessionConversionOptions(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    outputDir: str | None = Field(default=None)
    
    format: Literal['light', 'native', 'readable'] | None = Field(default=None)
    
    autoExecute: bool | None = Field(default=None)
    
    mergeReads: bool | None = Field(default=None)
    
    simplify: bool | None = Field(default=None)
    
    preserveThinking: bool | None = Field(default=None)
    



class WatchOptions(BaseModel):
    """"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    interval: float | None = Field(default=None)
    
    autoConvert: bool | None = Field(default=None)
    
    notifyOnNew: bool | None = Field(default=None)
    




# Type aliases that reference models


# Validation-related models moved from validation/ directory
# These are used by strawberry_domain.py for GraphQL type registration

class JsonDictValidation(BaseModel):
    """Empty model used as JSON container for validation"""
    model_config = ConfigDict(extra='forbid')


class RecordStringString(BaseModel):
    """Empty model for string-to-string mappings"""
    model_config = ConfigDict(extra='forbid')


class TemplatePreprocessor(BaseModel):
    """Configuration for template preprocessor"""
    model_config = ConfigDict(extra='forbid')

    function: str = Field(..., description='Function name to call, e.g. "build_context_from_ast"')
    module: str = Field(..., description='Python module path, e.g. "projects.codegen.code.shared.context_builders"')
    args: Optional['JsonDictValidation'] = Field(None,
                                                 description='Optional arguments passed as kwargs to the function')
