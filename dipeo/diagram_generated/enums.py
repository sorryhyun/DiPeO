"""
Generated enum definitions for DiPeO.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-10-04T16:50:38.989298
"""

from enum import Enum


class DataType(str, Enum):
    """"""
    
    ANY = "any"
    
    STRING = "string"
    
    NUMBER = "number"
    
    BOOLEAN = "boolean"
    
    OBJECT = "object"
    
    ARRAY = "array"
    


class ContentType(str, Enum):
    """"""
    
    RAW_TEXT = "raw_text"
    
    CONVERSATION_STATE = "conversation_state"
    
    OBJECT = "object"
    
    EMPTY = "empty"
    
    GENERIC = "generic"
    
    VARIABLE = "variable"
    
    BINARY = "binary"
    


class HandleDirection(str, Enum):
    """"""
    
    INPUT = "input"
    
    OUTPUT = "output"
    


class HandleLabel(str, Enum):
    """"""
    
    DEFAULT = "default"
    
    FIRST = "first"
    
    CONDTRUE = "condtrue"
    
    CONDFALSE = "condfalse"
    
    SUCCESS = "success"
    
    ERROR = "error"
    
    RESULTS = "results"
    


class DiagramFormat(str, Enum):
    """"""
    
    NATIVE = "native"
    
    LIGHT = "light"
    
    READABLE = "readable"
    


class Status(str, Enum):
    """"""
    
    PENDING = "pending"
    
    RUNNING = "running"
    
    PAUSED = "paused"
    
    COMPLETED = "completed"
    
    FAILED = "failed"
    
    ABORTED = "aborted"
    
    SKIPPED = "skipped"
    
    MAXITER_REACHED = "maxiter_reached"
    


class FlowStatus(str, Enum):
    """"""
    
    WAITING = "waiting"
    
    READY = "ready"
    
    RUNNING = "running"
    
    BLOCKED = "blocked"
    


class CompletionStatus(str, Enum):
    """"""
    
    SUCCESS = "success"
    
    FAILED = "failed"
    
    SKIPPED = "skipped"
    
    MAX_ITER = "max_iter"
    


class ExecutionPhase(str, Enum):
    """"""
    
    MEMORY_SELECTION = "memory_selection"
    
    DIRECT_EXECUTION = "direct_execution"
    
    DECISION_EVALUATION = "decision_evaluation"
    
    DEFAULT = "default"
    


class EventType(str, Enum):
    """"""
    
    EXECUTION_STARTED = "execution_started"
    
    EXECUTION_COMPLETED = "execution_completed"
    
    EXECUTION_ERROR = "execution_error"
    
    NODE_STARTED = "node_started"
    
    NODE_COMPLETED = "node_completed"
    
    NODE_ERROR = "node_error"
    
    NODE_OUTPUT = "node_output"
    
    EXECUTION_LOG = "execution_log"
    
    INTERACTIVE_PROMPT = "interactive_prompt"
    
    INTERACTIVE_RESPONSE = "interactive_response"
    


class LLMService(str, Enum):
    """"""
    
    OPENAI = "openai"
    
    ANTHROPIC = "anthropic"
    
    CLAUDE_CODE = "claude-code"
    
    CLAUDE_CODE_CUSTOM = "claude-code-custom"
    
    GOOGLE = "google"
    
    GEMINI = "gemini"
    
    OLLAMA = "ollama"
    


class APIServiceType(str, Enum):
    """"""
    
    OPENAI = "openai"
    
    ANTHROPIC = "anthropic"
    
    GOOGLE = "google"
    
    GEMINI = "gemini"
    
    OLLAMA = "ollama"
    
    CLAUDE_CODE = "claude-code"
    
    CLAUDE_CODE_CUSTOM = "claude-code-custom"
    


class ToolType(str, Enum):
    """"""
    
    WEB_SEARCH = "web_search"
    
    WEB_SEARCH_PREVIEW = "web_search_preview"
    
    IMAGE_GENERATION = "image_generation"
    


class ToolSelection(str, Enum):
    """"""
    
    NONE = "none"
    
    IMAGE = "image"
    
    WEBSEARCH = "websearch"
    


class AuthType(str, Enum):
    """"""
    
    NONE = "none"
    
    BEARER = "bearer"
    
    BASIC = "basic"
    
    API_KEY = "api_key"
    


class RetryStrategy(str, Enum):
    """"""
    
    NONE = "none"
    
    LINEAR = "linear"
    
    EXPONENTIAL = "exponential"
    
    FIBONACCI = "fibonacci"
    
    CONSTANT = "constant"
    
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    
    LINEAR_BACKOFF = "linear_backoff"
    
    FIXED_DELAY = "fixed_delay"
    


class DBBlockSubType(str, Enum):
    """"""
    
    FIXED_PROMPT = "fixed_prompt"
    
    FILE = "file"
    
    CODE = "code"
    
    API_TOOL = "api_tool"
    


class SupportedLanguage(str, Enum):
    """"""
    
    PYTHON = "python"
    
    TYPESCRIPT = "typescript"
    
    BASH = "bash"
    
    SHELL = "shell"
    


class HttpMethod(str, Enum):
    """"""
    
    GET = "get"
    
    POST = "post"
    
    PUT = "put"
    
    DELETE = "delete"
    
    PATCH = "patch"
    


class HookType(str, Enum):
    """"""
    
    SHELL = "shell"
    
    WEBHOOK = "webhook"
    
    PYTHON = "python"
    
    FILE = "file"
    


class HookTriggerMode(str, Enum):
    """"""
    
    NONE = "none"
    
    MANUAL = "manual"
    
    HOOK = "hook"
    


class ConditionType(str, Enum):
    """"""
    
    DETECT_MAX_ITERATIONS = "detect_max_iterations"
    
    CHECK_NODES_EXECUTED = "check_nodes_executed"
    
    CUSTOM = "custom"
    
    LLM_DECISION = "llm_decision"
    


class TemplateEngine(str, Enum):
    """"""
    
    INTERNAL = "internal"
    
    JINJA2 = "jinja2"
    


class NodeType(str, Enum):
    """"""
    
    START = "start"
    
    PERSON_JOB = "person_job"
    
    CONDITION = "condition"
    
    CODE_JOB = "code_job"
    
    API_JOB = "api_job"
    
    ENDPOINT = "endpoint"
    
    DB = "db"
    
    USER_RESPONSE = "user_response"
    
    HOOK = "hook"
    
    TEMPLATE_JOB = "template_job"
    
    JSON_SCHEMA_VALIDATOR = "json_schema_validator"
    
    TYPESCRIPT_AST = "typescript_ast"
    
    SUB_DIAGRAM = "sub_diagram"
    
    INTEGRATED_API = "integrated_api"
    
    IR_BUILDER = "ir_builder"
    
    DIFF_PATCH = "diff_patch"
    


class Severity(str, Enum):
    """"""
    
    ERROR = "error"
    
    WARNING = "warning"
    
    INFO = "info"
    


class EventPriority(str, Enum):
    """"""
    
    LOW = "low"
    
    NORMAL = "normal"
    
    HIGH = "high"
    
    CRITICAL = "critical"
    


class QueryOperationType(str, Enum):
    """"""
    
    QUERY = "query"
    
    MUTATION = "mutation"
    
    SUBSCRIPTION = "subscription"
    


class CrudOperation(str, Enum):
    """"""
    
    GET = "get"
    
    LIST = "list"
    
    CREATE = "create"
    
    UPDATE = "update"
    
    DELETE = "delete"
    
    SUBSCRIBE = "subscribe"
    


class QueryEntity(str, Enum):
    """"""
    
    DIAGRAM = "Diagram"
    
    PERSON = "Person"
    
    EXECUTION = "Execution"
    
    API_KEY = "ApiKey"
    
    CONVERSATION = "Conversation"
    
    FILE = "File"
    
    NODE = "Node"
    
    PROMPT_TEMPLATE = "PromptTemplate"
    
    SYSTEM = "System"
    


class FieldPreset(str, Enum):
    """"""
    
    MINIMAL = "minimal"
    
    STANDARD = "standard"
    
    DETAILED = "detailed"
    
    FULL = "full"
    


class FieldGroup(str, Enum):
    """"""
    
    METADATA = "metadata"
    
    TIMESTAMPS = "timestamps"
    
    RELATIONSHIPS = "relationships"
    
    CONFIGURATION = "configuration"
    



# Export all enums
__all__ = [
    
    "DataType",
    
    "ContentType",
    
    "HandleDirection",
    
    "HandleLabel",
    
    "DiagramFormat",
    
    "Status",
    
    "FlowStatus",
    
    "CompletionStatus",
    
    "ExecutionPhase",
    
    "EventType",
    
    "LLMService",
    
    "APIServiceType",
    
    "ToolType",
    
    "ToolSelection",
    
    "AuthType",
    
    "RetryStrategy",
    
    "DBBlockSubType",
    
    "SupportedLanguage",
    
    "HttpMethod",
    
    "HookType",
    
    "HookTriggerMode",
    
    "ConditionType",
    
    "TemplateEngine",
    
    "NodeType",
    
    "Severity",
    
    "EventPriority",
    
    "QueryOperationType",
    
    "CrudOperation",
    
    "QueryEntity",
    
    "FieldPreset",
    
    "FieldGroup",
    
]
