#!/usr/bin/env python3
# __generated__ by DiPeO
"""
Compatibility shim for domain_models.py
This file is part of the Phase 1 refactoring to eliminate monolithic files.
Domain models are kept here for backward compatibility while node data models
are re-exported from individual files in /models/ directory.

Phase 3 will split this into logical domain modules.
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Any, Dict, List, Literal, NewType, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from dipeo.domain.type_defs import JsonDict, JsonList, JsonPrimitive, JsonValue

from .enums import *
# Note: integrations are imported in __init__.py to avoid circular import


# NewType declarations
ApiKeyID = NewType('ApiKeyID', str)
ArrowID = NewType('ArrowID', str)
DiagramID = NewType('DiagramID', str)
ExecutionID = NewType('ExecutionID', str)
HandleID = NewType('HandleID', str)
HookID = NewType('HookID', str)
NodeID = NewType('NodeID', str)
PersonID = NewType('PersonID', str)
TaskID = NewType('TaskID', str)
CliSessionID = NewType('CliSessionID', str)
FileID = NewType('FileID', str)

class Vec2(BaseModel):
    """Vec2 model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    x: int
    y: int


class DomainHandle(BaseModel):
    """DomainHandle model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    id: HandleID
    node_id: NodeID
    label: HandleLabel
    direction: HandleDirection
    data_type: DataType
    position: str | None = Field(default=None)


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
    content_type: ContentType | None = Field(default=None)
    label: str | None = Field(default=None)
    packing: Literal["pack", "spread"] | None = Field(default=None)
    execution_priority: float | None = Field(default=None)
    data: dict[str, Any] | None = Field(default=None)


class PersonLLMConfig(BaseModel):
    """PersonLLMConfig model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    service: LLMService
    model: str
    api_key_id: ApiKeyID
    system_prompt: str | None = Field(default=None)
    prompt_file: str | None = Field(default=None)


class DomainPerson(BaseModel):
    """DomainPerson model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    id: PersonID
    label: str
    llm_config: PersonLLMConfig
    type: Literal["person"]


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

    id: DiagramID | None = Field(default=None)
    name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    version: str
    created: str
    modified: str
    author: str | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    format: str | None = Field(default=None)


class DomainDiagram(BaseModel):
    """DomainDiagram model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    nodes: list[DomainNode]
    handles: list[DomainHandle]
    arrows: list[DomainArrow]
    persons: list[DomainPerson]
    metadata: DiagramMetadata | None = Field(default=None)


class LLMUsage(BaseModel):
    """LLMUsage model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    input: int
    output: int
    cached: int | None = Field(default=None)
    total: int | None = Field(default=None)


class NodeState(BaseModel):
    """NodeState model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    status: Status
    started_at: str | None = Field(default=None)
    ended_at: str | None = Field(default=None)
    error: str | None = Field(default=None)
    llm_usage: LLMUsage | None = Field(default=None)
    output: dict[str, Any] | None = Field(default=None)


class NodeMetrics(BaseModel):
    """NodeMetrics model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    node_id: str
    node_type: str
    start_time: float
    end_time: float | None = Field(default=None)
    duration_ms: float | None = Field(default=None)
    memory_usage: float | None = Field(default=None)
    llm_usage: LLMUsage | None = Field(default=None)
    error: str | None = Field(default=None)
    dependencies: list[str] | None = Field(default=None)


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
    end_time: float | None = Field(default=None)
    total_duration_ms: float | None = Field(default=None)
    node_metrics: dict[str, NodeMetrics]
    critical_path: list[str] | None = Field(default=None)
    parallelizable_groups: list[list[str]] | None = Field(default=None)
    bottlenecks: list[Bottleneck] | None = Field(default=None)


class EnvelopeMeta(BaseModel):
    """EnvelopeMeta model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    node_id: str | None = Field(default=None)
    llm_usage: LLMUsage | None = Field(default=None)
    execution_time: float | None = Field(default=None)
    retry_count: float | None = Field(default=None)
    error: str | None = Field(default=None)
    error_type: str | None = Field(default=None)
    timestamp: str | float | None = Field(default=None)


class SerializedEnvelope(BaseModel):
    """SerializedEnvelope model"""
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
    representations: dict[str, Any] | None = Field(default=None)


class ExecutionState(BaseModel):
    """ExecutionState model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    id: ExecutionID
    status: Status
    diagram_id: DiagramID | None = Field(default=None)
    started_at: str
    ended_at: str | None = Field(default=None)
    node_states: dict[str, NodeState]
    node_outputs: dict[str, SerializedNodeOutput]
    llm_usage: LLMUsage
    error: str | None = Field(default=None)
    variables: JsonDict | None = Field(default=None)
    metadata: JsonDict | None = Field(default=None)
    duration_seconds: float | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    exec_counts: dict[str, float]
    executed_nodes: list[str]
    metrics: ExecutionMetrics | None = Field(default=None)


class ExecutionOptions(BaseModel):
    """ExecutionOptions model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    mode: Literal["normal", "debug", "monitor"] | None = Field(default=None)
    timeout: int | None = Field(default=None)
    variables: JsonDict | None = Field(default=None)
    debug: bool | None = Field(default=None)


class InteractivePromptData(BaseModel):
    """InteractivePromptData model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    node_id: NodeID
    prompt: str
    timeout: int | None = Field(default=None)
    default_value: str | None = Field(default=None)


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
    data: dict[str, Any] | None = Field(default=None)


class NodeDefinition(BaseModel):
    """NodeDefinition model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    type: str
    node_schema: Any
    handler: Any
    requires_services: list[str] | None = Field(default=None)
    description: str | None = Field(default=None)


class Message(BaseModel):
    """Base message interface for conversations
Used by both execution (PersonMemory) and person domains"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    id: str | None = Field(default=None)
    from_person_id: PersonID | Literal["system"]
    to_person_id: PersonID
    content: str
    timestamp: str | None = Field(default=None)
    token_count: float | None = Field(default=None)
    message_type: Literal["person_to_person", "system_to_person", "person_to_system"]
    metadata: JsonDict | None = Field(default=None)


class ConversationMetadata(BaseModel):
    """ConversationMetadata model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    started_at: str
    last_message_at: str
    total_tokens: float
    message_count: float
    context_resets: float


class Conversation(BaseModel):
    """Conversation model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    messages: list[Message]
    metadata: ConversationMetadata | None = Field(default=None)


class CliSession(BaseModel):
    """CLI session for terminal operations"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    id: CliSessionID
    session_id: str
    user_id: str | None = Field(default=None)
    started_at: str
    last_active: str | None = Field(default=None)
    status: Literal['active', 'inactive', 'terminated']
    metadata: dict[str, Any] | None = Field(default=None)
    current_directory: str | None = Field(default=None)
    environment: dict[str, str] | None = Field(default=None)


class CliSessionResult(BaseModel):
    """Result of CLI session operations"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    success: bool
    session: CliSession | None = Field(default=None)
    message: str | None = Field(default=None)
    error: str | None = Field(default=None)


class File(BaseModel):
    """File representation for diagram operations and storage"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    id: FileID
    name: str
    path: str
    content: str | None = Field(default=None)
    size: int | None = Field(default=None)
    mime_type: str | None = Field(default=None)
    created_at: str | None = Field(default=None)
    modified_at: str | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)


class FileOperationResult(BaseModel):
    """Result of file operations"""
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
    config: dict[str, Any] | None = Field(default=None)


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
    width: int | None = Field(default=None)
    height: int | None = Field(default=None)


class ToolOutput(BaseModel):
    """ToolOutput model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    type: ToolType
    result: list[WebSearchResult] | ImageGenerationResult | Any
    raw_response: Any | None = Field(default=None)


class ChatResult(BaseModel):
    """ChatResult model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    text: str
    llm_usage: LLMUsage | None = Field(default=None)
    raw_response: Any | None = Field(default=None)
    tool_outputs: list[ToolOutput] | None = Field(default=None)


class LLMRequestOptions(BaseModel):
    """LLMRequestOptions model"""
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    temperature: float | None = Field(default=None)
    max_tokens: float | None = Field(default=None)
    top_p: float | None = Field(default=None)
    n: float | None = Field(default=None)
    tools: list[ToolConfig] | None = Field(default=None)
    response_format: Any | None = Field(default=None)


# Type aliases that reference models
SerializedNodeOutput = SerializedEnvelope
PersonMemoryMessage = Message


def parse_handle_id(handle_id: str) -> tuple[NodeID, str, str]:
    """Parse a handle ID into its components."""
    parts = handle_id.split('_')
    if len(parts) < 3:
        raise ValueError(f"Invalid handle ID format: {handle_id}")

    node_id = parts[0]
    direction = parts[-1]
    label = '_'.join(parts[1:-1])

    return NodeID(node_id), label, direction


def create_handle_id(node_id: NodeID, label: str, direction: str) -> HandleID:
    """Create a handle ID from components."""
    return HandleID(f"{node_id}_{label}_{direction}")


# Type guard functions
def is_vec2(obj: Any) -> bool:
    """Check if object is a Vec2."""
    return isinstance(obj, Vec2)


def is_domain_handle(obj: Any) -> bool:
    """Check if object is a DomainHandle."""
    return isinstance(obj, DomainHandle)


def is_domain_node(obj: Any) -> bool:
    """Check if object is a DomainNode."""
    return isinstance(obj, DomainNode)


def is_domain_arrow(obj: Any) -> bool:
    """Check if object is a DomainArrow."""
    return isinstance(obj, DomainArrow)


def is_person_llm_config(obj: Any) -> bool:
    """Check if object is a PersonLLMConfig."""
    return isinstance(obj, PersonLLMConfig)


def is_domain_person(obj: Any) -> bool:
    """Check if object is a DomainPerson."""
    return isinstance(obj, DomainPerson)


def is_domain_api_key(obj: Any) -> bool:
    """Check if object is a DomainApiKey."""
    return isinstance(obj, DomainApiKey)


def is_diagram_metadata(obj: Any) -> bool:
    """Check if object is a DiagramMetadata."""
    return isinstance(obj, DiagramMetadata)


def is_domain_diagram(obj: Any) -> bool:
    """Check if object is a DomainDiagram."""
    return isinstance(obj, DomainDiagram)


def is_llm_usage(obj: Any) -> bool:
    """Check if object is a LLMUsage."""
    return isinstance(obj, LLMUsage)


def is_node_state(obj: Any) -> bool:
    """Check if object is a NodeState."""
    return isinstance(obj, NodeState)


def is_node_metrics(obj: Any) -> bool:
    """Check if object is a NodeMetrics."""
    return isinstance(obj, NodeMetrics)


def is_bottleneck(obj: Any) -> bool:
    """Check if object is a Bottleneck."""
    return isinstance(obj, Bottleneck)


def is_execution_metrics(obj: Any) -> bool:
    """Check if object is a ExecutionMetrics."""
    return isinstance(obj, ExecutionMetrics)


def is_envelope_meta(obj: Any) -> bool:
    """Check if object is a EnvelopeMeta."""
    return isinstance(obj, EnvelopeMeta)


def is_serialized_envelope(obj: Any) -> bool:
    """Check if object is a SerializedEnvelope."""
    return isinstance(obj, SerializedEnvelope)


def is_execution_state(obj: Any) -> bool:
    """Check if object is a ExecutionState."""
    return isinstance(obj, ExecutionState)


def is_execution_options(obj: Any) -> bool:
    """Check if object is a ExecutionOptions."""
    return isinstance(obj, ExecutionOptions)


def is_interactive_prompt_data(obj: Any) -> bool:
    """Check if object is a InteractivePromptData."""
    return isinstance(obj, InteractivePromptData)


def is_interactive_response(obj: Any) -> bool:
    """Check if object is a InteractiveResponse."""
    return isinstance(obj, InteractiveResponse)


def is_execution_update(obj: Any) -> bool:
    """Check if object is a ExecutionUpdate."""
    return isinstance(obj, ExecutionUpdate)


def is_node_definition(obj: Any) -> bool:
    """Check if object is a NodeDefinition."""
    return isinstance(obj, NodeDefinition)


def is_message(obj: Any) -> bool:
    """Check if object is a Message."""
    return isinstance(obj, Message)


def is_conversation_metadata(obj: Any) -> bool:
    """Check if object is a ConversationMetadata."""
    return isinstance(obj, ConversationMetadata)


def is_conversation(obj: Any) -> bool:
    """Check if object is a Conversation."""
    return isinstance(obj, Conversation)


def is_tool_config(obj: Any) -> bool:
    """Check if object is a ToolConfig."""
    return isinstance(obj, ToolConfig)


def is_web_search_result(obj: Any) -> bool:
    """Check if object is a WebSearchResult."""
    return isinstance(obj, WebSearchResult)


def is_image_generation_result(obj: Any) -> bool:
    """Check if object is a ImageGenerationResult."""
    return isinstance(obj, ImageGenerationResult)


def is_tool_output(obj: Any) -> bool:
    """Check if object is a ToolOutput."""
    return isinstance(obj, ToolOutput)


def is_chat_result(obj: Any) -> bool:
    """Check if object is a ChatResult."""
    return isinstance(obj, ChatResult)


def is_llm_request_options(obj: Any) -> bool:
    """Check if object is a LLMRequestOptions."""
    return isinstance(obj, LLMRequestOptions)


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


class NodeUpdate(BaseModel):
    """Node update payload for node-specific updates"""
    model_config = ConfigDict(extra='forbid')

    execution_id: ExecutionID
    node_id: NodeID
    status: Status
    progress: Optional[float] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    timestamp: str


class InteractivePrompt(BaseModel):
    """Interactive prompt payload for user interaction requests"""
    model_config = ConfigDict(extra='forbid')

    execution_id: ExecutionID
    node_id: NodeID
    prompt_id: str
    prompt: str
    timeout: Optional[float] = None
    default_value: Optional[str] = None
    options: Optional[List[str]] = None
    timestamp: str


class ExecutionLogEntry(BaseModel):
    """Execution log entry for real-time log streaming"""
    model_config = ConfigDict(extra='forbid')

    execution_id: ExecutionID
    node_id: Optional[NodeID] = None
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    message: str
    context: Optional[Dict[str, Any]] = None
    timestamp: str


class KeepalivePayload(BaseModel):
    """Keepalive payload for connection maintenance"""
    model_config = ConfigDict(extra='forbid')

    type: Literal['keepalive']
    timestamp: str


# Constants from TypeScript
PROVIDER_OPERATIONS = {
    "\u0027github\u0027": ["create_issue", "update_issue", "list_issues", "create_pr", "merge_pr", "get_repo_info"],
    "\u0027google_search\u0027": ["search"],
    "\u0027jira\u0027": ["create_issue", "update_issue", "search_issues", "transition_issue", "add_comment"],
    "\u0027notion\u0027": ["create_page", "update_page", "read_page", "delete_page", "create_database",
                           "query_database", "update_database"],
    "\u0027slack\u0027": ["send_message", "read_channel", "create_channel", "list_channels", "upload_file"]}