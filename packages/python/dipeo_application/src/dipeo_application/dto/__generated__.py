"""
Generated DTOs for application layer.
DO NOT EDIT DIRECTLY - Generated from TypeScript domain models.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any, NewType
from enum import Enum
from datetime import datetime

# Common DTOs
@dataclass
class ConversationMetadata:
    started_at: str
    last_message_at: str
    total_tokens: float
    message_count: float
    context_resets: float

@dataclass
class Conversation:
    messages: List[Message]
    metadata: Optional[Optional[ConversationMetadata]] = None

@dataclass
class MemoryState:
    visible_messages: float
    has_more: Optional[Optional[bool]] = None
    config: Optional[Optional[MemoryConfig]] = None

@dataclass
class Vec2:
    x: float
    y: float

@dataclass
class DomainHandle:
    id: HandleID
    node_id: NodeID
    label: str
    direction: HandleDirection
    data_type: DataType
    position: Optional[Union[str, None, None]] = None

@dataclass
class DomainNode:
    id: NodeID
    type: NodeType
    position: Vec2
    data: Dict[str, Any]
    display_name: Optional[Optional[str]] = None

@dataclass
class DomainArrow:
    id: ArrowID
    source: HandleID
    target: HandleID
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemoryConfig:
    pass
    forget_mode: Optional[Optional[ForgettingMode]] = None
    max_messages: Optional[Optional[float]] = None
    temperature: Optional[Optional[float]] = None

@dataclass
class DomainPerson:
    id: PersonID
    label: str
    service: LLMService
    model: str
    type: 'person'
    api_key_id: Optional[Union[ApiKeyID, None, None]] = None
    system_prompt: Optional[Union[str, None, None]] = None
    masked_api_key: Optional[Union[str, None, None]] = None

@dataclass
class DomainApiKey:
    id: ApiKeyID
    label: str
    service: LLMService
    masked_key: str
    key: Optional[Optional[str]] = None

@dataclass
class DiagramMetadata:
    version: str
    created: str
    modified: str
    id: Optional[Union[DiagramID, None, None]] = None
    name: Optional[Union[str, None, None]] = None
    description: Optional[Union[str, None, None]] = None
    author: Optional[Union[str, None, None]] = None
    tags: Optional[Union[List[str], None, None]] = None

@dataclass
class DomainDiagram:
    nodes: List[DomainNode]
    handles: List[DomainHandle]
    arrows: List[DomainArrow]
    persons: List[DomainPerson]
    metadata: Optional[Union[DiagramMetadata, None, None]] = None

@dataclass
class BaseNodeData:
    label: str
    flipped: Optional[Optional[bool]] = None

@dataclass
class StartNodeData:
    custom_data: Dict[str, Union[str, float, bool]]
    output_data_structure: Dict[str, str]

@dataclass
class ConditionNodeData:
    condition_type: str
    expression: Optional[Optional[str]] = None
    node_indices: Optional[Optional[List[str]]] = None

@dataclass
class PersonJobNodeData:
    first_only_prompt: str
    max_iteration: float
    person: Optional[Optional[PersonID]] = None
    default_prompt: Optional[Optional[str]] = None
    memory_config: Optional[Union[MemoryConfig, None, None]] = None

@dataclass
class EndpointNodeData:
    save_to_file: bool
    file_name: Optional[Optional[str]] = None

@dataclass
class DBNodeData:
    sub_type: DBBlockSubType
    operation: str
    file: Optional[Optional[str]] = None
    collection: Optional[Optional[str]] = None
    query: Optional[Optional[str]] = None
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class JobNodeData:
    code_type: SupportedLanguage
    code: str

@dataclass
class NotionNodeData:
    operation: NotionOperation
    page_id: Optional[Optional[str]] = None
    database_id: Optional[Optional[str]] = None

class NodeType(str, Enum):
    START = "start"
    PERSON_JOB = "person_job"
    CONDITION = "condition"
    JOB = "job"
    ENDPOINT = "endpoint"
    DB = "db"
    USER_RESPONSE = "user_response"
    NOTION = "notion"
    PERSON_BATCH_JOB = "person_batch_job"

class HandleDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"

class DataType(str, Enum):
    ANY = "any"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"

class ForgettingMode(str, Enum):
    NO_FORGET = "no_forget"
    ON_EVERY_TURN = "on_every_turn"
    UPON_REQUEST = "upon_request"

class DiagramFormat(str, Enum):
    NATIVE = "native"
    LIGHT = "light"
    READABLE = "readable"

class DBBlockSubType(str, Enum):
    FIXED_PROMPT = "fixed_prompt"
    FILE = "file"
    CODE = "code"
    API_TOOL = "api_tool"

class ContentType(str, Enum):
    VARIABLE = "variable"
    RAW_TEXT = "raw_text"
    CONVERSATION_STATE = "conversation_state"

class SupportedLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    BASH = "bash"

@dataclass
class NodeID:
    pass

@dataclass
class ArrowID:
    pass

@dataclass
class HandleID:
    pass

@dataclass
class PersonID:
    pass

@dataclass
class ApiKeyID:
    pass

@dataclass
class DiagramID:
    pass

@dataclass
class PersonBatchJobNodeData:
    pass

@dataclass
class TokenUsage:
    input: float
    output: float
    cached: Optional[Union[float, None, None]] = None
    total: Optional[Optional[float]] = None

@dataclass
class NodeState:
    status: NodeExecutionStatus
    started_at: Optional[Union[str, None, None]] = None
    ended_at: Optional[Union[str, None, None]] = None
    error: Optional[Union[str, None, None]] = None
    token_usage: Optional[Union[TokenUsage, None, None]] = None

@dataclass
class NodeOutput:
    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionState:
    id: ExecutionID
    status: ExecutionStatus
    started_at: str
    node_states: Dict[str, NodeState]
    node_outputs: Dict[str, NodeOutput]
    token_usage: TokenUsage
    variables: Dict[str, Any]
    diagram_id: Optional[Union[DiagramID, None, None]] = None
    ended_at: Optional[Union[str, None, None]] = None
    error: Optional[Union[str, None, None]] = None
    duration_seconds: Optional[Union[float, None, None]] = None
    is_active: Optional[Optional[bool]] = None

@dataclass
class ExecutionOptions:
    pass
    mode: Optional[Union['normal', 'debug', 'monitor', None]] = None
    timeout: Optional[Optional[float]] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    debug: Optional[Optional[bool]] = None

@dataclass
class InteractivePromptData:
    node_id: NodeID
    prompt: str
    timeout: Optional[Optional[float]] = None
    default_value: Optional[Union[str, None, None]] = None

@dataclass
class NodeDefinition:
    type: str
    node_schema: Any
    handler: Any
    requires_services: Optional[Optional[List[str]]] = None
    description: Optional[Optional[str]] = None

class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    SKIPPED = "SKIPPED"

class NodeExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    SKIPPED = "SKIPPED"

@dataclass
class ExecutionID:
    pass

@dataclass
class PersonMemoryState:
    pass

@dataclass
class PersonMemoryConfig:
    pass

class LLMService(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROK = "grok"
    BEDROCK = "bedrock"
    VERTEX = "vertex"
    DEEPSEEK = "deepseek"

class NotionOperation(str, Enum):
    CREATE_PAGE = "create_page"
    UPDATE_PAGE = "update_page"
    READ_PAGE = "read_page"
    DELETE_PAGE = "delete_page"
    CREATE_DATABASE = "create_database"
    QUERY_DATABASE = "query_database"
    UPDATE_DATABASE = "update_database"


# Request DTOs
@dataclass
class ExecutionUpdateRequest:
    type: EventType
    execution_id: ExecutionID
    node_id: Optional[Optional[NodeID]] = None
    status: Optional[Optional[NodeExecutionStatus]] = None
    result: Optional[Any] = None
    error: Optional[Optional[str]] = None
    timestamp: Optional[Optional[str]] = None
    total_tokens: Optional[Optional[float]] = None
    node_type: Optional[Optional[str]] = None
    tokens: Optional[Optional[float]] = None
    data: Dict[str, Any] = field(default_factory=dict)


# Response DTOs
@dataclass
class UserResponseNodeDataResponse:
    prompt: str
    timeout: float

@dataclass
class InteractiveResponseResponse:
    node_id: NodeID
    response: str
    timestamp: str


# Event DTOs
@dataclass
class MessageEvent:
    person_id: PersonID
    role: Union['user', 'assistant', 'system']
    content: str
    id: Optional[Optional[str]] = None
    timestamp: Optional[Optional[str]] = None
    token_count: Optional[Optional[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class EventTypeEvent(str, Enum):
    EXECUTION_STATUS_CHANGED = "EXECUTION_STATUS_CHANGED"
    NODE_STATUS_CHANGED = "NODE_STATUS_CHANGED"
    NODE_PROGRESS = "NODE_PROGRESS"
    INTERACTIVE_PROMPT = "INTERACTIVE_PROMPT"
    INTERACTIVE_RESPONSE = "INTERACTIVE_RESPONSE"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    EXECUTION_UPDATE = "EXECUTION_UPDATE"

@dataclass
class PersonMemoryMessageEvent:
    pass


# Utility functions
def generate_id(prefix: str) -> str:
    """Generate a unique ID with the given prefix."""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def generate_node_id() -> str:
    return generate_id("node")

def generate_diagram_id() -> str:
    return generate_id("diagram")

def generate_person_id() -> str:
    return generate_id("person")
