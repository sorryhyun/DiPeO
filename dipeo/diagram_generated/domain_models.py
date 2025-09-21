#!/usr/bin/env python3
# __generated__ by DiPeO
"""
Domain models generated from TypeScript interfaces.
Generated at: 2025-09-21T20:14:15.539774
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
    """CliSession model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: CliSessionID
    
    session_id: str
    
    user_id: str | None = Field(default=None)
    
    started_at: str
    
    status: Literal['active', 'inactive', 'terminated']
    
    metadata: Dict[str, Any] | None = Field(default=None)
    
    environment: Dict[str, str] | None = Field(default=None)
    



class CliSessionResult(BaseModel):
    """CliSessionResult model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    success: bool
    
    session: CliSession | None = Field(default=None)
    
    message: str | None = Field(default=None)
    
    error: str | None = Field(default=None)
    



class Message(BaseModel):
    """Message model"""
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
    """ConversationMetadata model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    started_at: str
    
    total_tokens: float
    
    message_count: float
    



class Conversation(BaseModel):
    """Conversation model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    messages: List[Message]
    
    metadata: ConversationMetadata | None = Field(default=None)
    



class Vec2(BaseModel):
    """Vec2 model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    x: float
    
    y: float
    



class DomainHandle(BaseModel):
    """DomainHandle model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: HandleID
    
    node_id: NodeID
    
    label: HandleLabel
    
    direction: HandleDirection
    
    data_type: DataType
    
    position: Optional[str] | None = Field(default=None)
    



class DomainNode(BaseModel):
    """DomainNode model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: NodeID
    
    type: NodeType
    
    position: Vec2
    
    data: JsonDict
    



class DomainArrow(BaseModel):
    """DomainArrow model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: ArrowID
    
    source: HandleID
    
    target: HandleID
    
    content_type: Optional[ContentType] | None = Field(default=None)
    
    label: Optional[str] | None = Field(default=None)
    
    execution_priority: Optional[float] | None = Field(default=None)
    
    data: Optional[Dict[str, Any]] | None = Field(default=None)
    



class PersonLLMConfig(BaseModel):
    """PersonLLMConfig model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    service: LLMService
    
    model: str
    
    api_key_id: ApiKeyID
    
    system_prompt: Optional[str] | None = Field(default=None)
    
    prompt_file: Optional[str] | None = Field(default=None)
    



class DomainPerson(BaseModel):
    """DomainPerson model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: PersonID
    
    label: str
    
    llm_config: PersonLLMConfig
    
    type: Literal['person']
    



class DomainApiKey(BaseModel):
    """DomainApiKey model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    id: ApiKeyID
    
    label: str
    
    service: APIServiceType
    
    key: str | None = Field(default=None)
    



class DiagramMetadata(BaseModel):
    """DiagramMetadata model"""
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
    """DomainDiagram model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    nodes: List[DomainNode]
    
    handles: List[DomainHandle]
    
    arrows: List[DomainArrow]
    
    persons: List[DomainPerson]
    
    metadata: Optional[DiagramMetadata] | None = Field(default=None)
    



class LLMUsage(BaseModel):
    """LLMUsage model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    input: float
    
    output: float
    
    cached: Optional[float] | None = Field(default=None)
    
    total: float | None = Field(default=None)
    



class NodeState(BaseModel):
    """NodeState model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    status: Status
    
    started_at: Optional[str] | None = Field(default=None)
    
    ended_at: Optional[str] | None = Field(default=None)
    
    error: Optional[str] | None = Field(default=None)
    
    llm_usage: Optional[LLMUsage] | None = Field(default=None)
    
    output: Optional[Dict[str, Any]] | None = Field(default=None)
    



class NodeMetrics(BaseModel):
    """NodeMetrics model"""
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
    """Bottleneck model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    node_id: str
    
    node_type: str
    
    duration_ms: float
    
    percentage: float
    



class ExecutionMetrics(BaseModel):
    """ExecutionMetrics model"""
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
    """EnvelopeMeta model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    node_id: str | None = Field(default=None)
    
    llm_usage: LLMUsage | None = Field(default=None)
    
    execution_time: float | None = Field(default=None)
    
    retry_count: float | None = Field(default=None)
    
    error: str | None = Field(default=None)
    
    error_type: str | None = Field(default=None)
    
    timestamp: Union[str, float] | None = Field(default=None)
    



class SerializedEnvelope(BaseModel):
    """SerializedEnvelope model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    envelope_format: Literal[True] = Field(default=True)
    
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
    """ExecutionState model"""
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
    """ExecutionOptions model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    mode: Literal['normal', 'debug', 'monitor'] | None = Field(default=None)
    
    timeout: float | None = Field(default=None)
    
    variables: JsonDict | None = Field(default=None)
    
    debug: bool | None = Field(default=None)
    



class InteractivePromptData(BaseModel):
    """InteractivePromptData model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    node_id: NodeID
    
    prompt: str
    
    timeout: float | None = Field(default=None)
    
    default_value: Optional[str] | None = Field(default=None)
    



class InteractiveResponse(BaseModel):
    """InteractiveResponse model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    node_id: NodeID
    
    response: str
    
    timestamp: str
    



class ExecutionUpdate(BaseModel):
    """ExecutionUpdate model"""
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
    """NodeDefinition model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: str
    
    handler: Any
    
    requires_services: List[str] | None = Field(default=None)
    
    description: str | None = Field(default=None)
    



class File(BaseModel):
    """File model"""
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
    """FileOperationResult model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    success: bool
    
    file: File | None = Field(default=None)
    
    message: str | None = Field(default=None)
    
    error: str | None = Field(default=None)
    



class ToolConfig(BaseModel):
    """ToolConfig model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: ToolType
    
    enabled: bool | None = Field(default=None)
    
    config: Dict[str, Any] | None = Field(default=None)
    



class WebSearchResult(BaseModel):
    """WebSearchResult model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    url: str
    
    title: str
    
    snippet: str
    
    score: float | None = Field(default=None)
    



class ImageGenerationResult(BaseModel):
    """ImageGenerationResult model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    image_data: str
    
    format: str
    
    width: float | None = Field(default=None)
    
    height: float | None = Field(default=None)
    



class ToolOutput(BaseModel):
    """ToolOutput model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: ToolType
    
    result: Union[List[WebSearchResult], ImageGenerationResult, Any]
    
    raw_response: Any | None = Field(default=None)
    



class ChatResult(BaseModel):
    """ChatResult model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    text: str
    
    llm_usage: Optional[LLMUsage] | None = Field(default=None)
    
    raw_response: Optional[Any] | None = Field(default=None)
    
    tool_outputs: Optional[List[ToolOutput]] | None = Field(default=None)
    



class LLMRequestOptions(BaseModel):
    """LLMRequestOptions model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    temperature: float | None = Field(default=None)
    
    max_tokens: float | None = Field(default=None)
    
    top_p: float | None = Field(default=None)
    
    n: float | None = Field(default=None)
    
    tools: List[ToolConfig] | None = Field(default=None)
    
    response_format: Any | None = Field(default=None)
    



class NodeUpdate(BaseModel):
    """NodeUpdate model"""
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
    """InteractivePrompt model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    execution_id: ExecutionID
    
    node_id: NodeID
    
    prompt: str
    
    timeout: float | None = Field(default=None)
    
    default_value: Optional[str] | None = Field(default=None)
    
    options: List[str] | None = Field(default=None)
    
    timestamp: str
    



class ExecutionLogEntry(BaseModel):
    """ExecutionLogEntry model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    execution_id: ExecutionID
    
    node_id: NodeID | None = Field(default=None)
    
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    message: str
    
    context: Dict[str, Any] | None = Field(default=None)
    
    timestamp: str
    



class KeepalivePayload(BaseModel):
    """KeepalivePayload model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: Literal['keepalive']
    
    timestamp: str
    



class ClaudeCodeSession(BaseModel):
    """ClaudeCodeSession model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    session_id: str
    
    events: List[SessionEvent]
    
    metadata: SessionMetadata
    



class SessionEvent(BaseModel):
    """SessionEvent model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    type: Literal['user', 'assistant', 'summary']
    
    uuid: str
    
    parent_uuid: str | None = Field(default=None)
    
    timestamp: str
    
    message: ClaudeCodeMessage
    
    tool_use: ToolUse | None = Field(default=None)
    
    tool_result: ToolResult | None = Field(default=None)
    



class ClaudeCodeMessage(BaseModel):
    """ClaudeCodeMessage model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    role: Literal['user', 'assistant']
    
    content: str
    



class SessionMetadata(BaseModel):
    """SessionMetadata model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    start_time: str
    
    end_time: str | None = Field(default=None)
    
    total_events: float
    
    tool_usage_count: Dict[str, float]
    
    project_path: str | None = Field(default=None)
    



class ToolUse(BaseModel):
    """ToolUse model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    name: str
    
    input: Dict[str, Any]
    



class ToolResult(BaseModel):
    """ToolResult model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    success: bool
    
    output: str | None = Field(default=None)
    
    error: str | None = Field(default=None)
    



class ConversationTurn(BaseModel):
    """ConversationTurn model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    user_event: SessionEvent
    
    assistant_event: SessionEvent
    
    tool_events: List[SessionEvent]
    



class DiffPatchInput(BaseModel):
    """DiffPatchInput model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    file_path: str
    
    old_content: str | None = Field(default=None)
    
    new_content: str | None = Field(default=None)
    
    patch: str | None = Field(default=None)
    



class ClaudeCodeDiagramMetadata(BaseModel):
    """ClaudeCodeDiagramMetadata model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    session_id: str
    
    created_at: str
    
    event_count: float
    
    node_count: float
    
    tool_usage: Dict[str, float]
    



class SessionStatistics(BaseModel):
    """SessionStatistics model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    session_id: str
    
    total_events: float
    
    user_prompts: float
    
    assistant_responses: float
    
    total_tool_calls: float
    
    tool_breakdown: Dict[str, float]
    
    duration: float | None = Field(default=None)
    
    files_modified: List[str]
    
    commands_executed: List[str]
    



class SessionConversionOptions(BaseModel):
    """SessionConversionOptions model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    output_dir: str | None = Field(default=None)
    
    format: Literal['light', 'native', 'readable'] | None = Field(default=None)
    
    auto_execute: bool | None = Field(default=None)
    
    merge_reads: bool | None = Field(default=None)
    
    simplify: bool | None = Field(default=None)
    
    preserve_thinking: bool | None = Field(default=None)
    



class WatchOptions(BaseModel):
    """WatchOptions model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    
    interval: float | None = Field(default=None)
    
    auto_convert: bool | None = Field(default=None)
    
    notify_on_new: bool | None = Field(default=None)
    




# Type aliases that reference models

SerializedNodeOutput = SerializedEnvelope

PersonMemoryMessage = Message


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
