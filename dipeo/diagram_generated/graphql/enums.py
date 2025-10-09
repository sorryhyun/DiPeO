"""
Generated Strawberry GraphQL enum definitions for DiPeO.
Avoid editing THIS FILE DIRECTLY.

Generated at: 2025-10-09T15:58:04.745152
"""

from enum import Enum
import strawberry


@strawberry.enum
class QueryOperationTypeGraphQL(Enum):
    """GraphQL enum for QueryOperationType"""
    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"


@strawberry.enum
class CrudOperationGraphQL(Enum):
    """GraphQL enum for CrudOperation"""
    GET = "get"
    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SUBSCRIBE = "subscribe"


@strawberry.enum
class QueryEntityGraphQL(Enum):
    """GraphQL enum for QueryEntity"""
    DIAGRAM = "Diagram"
    PERSON = "Person"
    EXECUTION = "Execution"
    API_KEY = "ApiKey"
    CONVERSATION = "Conversation"
    FILE = "File"
    NODE = "Node"
    PROMPT_TEMPLATE = "PromptTemplate"
    SYSTEM = "System"


@strawberry.enum
class FieldPresetGraphQL(Enum):
    """GraphQL enum for FieldPreset"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"
    FULL = "full"


@strawberry.enum
class FieldGroupGraphQL(Enum):
    """GraphQL enum for FieldGroup"""
    METADATA = "metadata"
    TIMESTAMPS = "timestamps"
    RELATIONSHIPS = "relationships"
    CONFIGURATION = "configuration"


@strawberry.enum
class GraphQLScalarGraphQL(Enum):
    """GraphQL enum for GraphQLScalar"""
    ID = "ID"
    STRING = "String"
    INT = "Int"
    FLOAT = "Float"
    BOOLEAN = "Boolean"
    JSON = "JSON"
    DATE_TIME = "DateTime"
    UPLOAD = "Upload"


@strawberry.enum
class DiPeOBrandedScalarGraphQL(Enum):
    """GraphQL enum for DiPeOBrandedScalar"""
    DIAGRAM_ID = "DiagramID"
    NODE_ID = "NodeID"
    ARROW_ID = "ArrowID"
    HANDLE_ID = "HandleID"
    PERSON_ID = "PersonID"
    API_KEY_ID = "ApiKeyID"
    EXECUTION_ID = "ExecutionID"
    TASK_ID = "TaskID"
    HOOK_ID = "HookID"


@strawberry.enum
class DataTypeGraphQL(Enum):
    """GraphQL enum for DataType"""
    ANY = "any"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@strawberry.enum
class ContentTypeGraphQL(Enum):
    """GraphQL enum for ContentType"""
    RAW_TEXT = "raw_text"
    CONVERSATION_STATE = "conversation_state"
    OBJECT = "object"
    EMPTY = "empty"
    GENERIC = "generic"
    VARIABLE = "variable"
    BINARY = "binary"


@strawberry.enum
class HandleDirectionGraphQL(Enum):
    """GraphQL enum for HandleDirection"""
    INPUT = "input"
    OUTPUT = "output"


@strawberry.enum
class HandleLabelGraphQL(Enum):
    """GraphQL enum for HandleLabel"""
    DEFAULT = "default"
    FIRST = "first"
    CONDTRUE = "condtrue"
    CONDFALSE = "condfalse"
    SUCCESS = "success"
    ERROR = "error"
    RESULTS = "results"


@strawberry.enum
class DiagramFormatGraphQL(Enum):
    """GraphQL enum for DiagramFormat"""
    YAML = "yaml"
    JSON = "json"
    LIGHT = "light"


@strawberry.enum
class StatusGraphQL(Enum):
    """GraphQL enum for Status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    SKIPPED = "skipped"
    MAXITER_REACHED = "maxiter_reached"


@strawberry.enum
class FlowStatusGraphQL(Enum):
    """GraphQL enum for FlowStatus"""
    WAITING = "waiting"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"


@strawberry.enum
class CompletionStatusGraphQL(Enum):
    """GraphQL enum for CompletionStatus"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    MAX_ITER = "max_iter"


@strawberry.enum
class ExecutionPhaseGraphQL(Enum):
    """GraphQL enum for ExecutionPhase"""
    MEMORY_SELECTION = "memory_selection"
    DIRECT_EXECUTION = "direct_execution"
    DECISION_EVALUATION = "decision_evaluation"
    DEFAULT = "default"


@strawberry.enum
class EventTypeGraphQL(Enum):
    """GraphQL enum for EventType"""
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


@strawberry.enum
class LLMServiceGraphQL(Enum):
    """GraphQL enum for LLMService"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CLAUDE_CODE = "claude-code"
    CLAUDE_CODE_CUSTOM = "claude-code-custom"
    GOOGLE = "google"
    GEMINI = "gemini"
    OLLAMA = "ollama"


@strawberry.enum
class APIServiceTypeGraphQL(Enum):
    """GraphQL enum for APIServiceType"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    CLAUDE_CODE = "claude-code"
    CLAUDE_CODE_CUSTOM = "claude-code-custom"


@strawberry.enum
class ToolTypeGraphQL(Enum):
    """GraphQL enum for ToolType"""
    WEB_SEARCH = "web_search"
    WEB_SEARCH_PREVIEW = "web_search_preview"
    IMAGE_GENERATION = "image_generation"


@strawberry.enum
class ToolSelectionGraphQL(Enum):
    """GraphQL enum for ToolSelection"""
    NONE = "none"
    IMAGE = "image"
    WEBSEARCH = "websearch"


@strawberry.enum
class AuthTypeGraphQL(Enum):
    """GraphQL enum for AuthType"""
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    API_KEY = "api_key"


@strawberry.enum
class RetryStrategyGraphQL(Enum):
    """GraphQL enum for RetryStrategy"""
    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"
    CONSTANT = "constant"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"


@strawberry.enum
class DBBlockSubTypeGraphQL(Enum):
    """GraphQL enum for DBBlockSubType"""
    FIXED_PROMPT = "fixed_prompt"
    FILE = "file"
    CODE = "code"
    API_TOOL = "api_tool"


@strawberry.enum
class DBOperationGraphQL(Enum):
    """GraphQL enum for DBOperation"""
    PROMPT = "prompt"
    READ = "read"
    WRITE = "write"
    APPEND = "append"
    UPDATE = "update"


@strawberry.enum
class SupportedLanguageGraphQL(Enum):
    """GraphQL enum for SupportedLanguage"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    BASH = "bash"
    SHELL = "shell"


@strawberry.enum
class HttpMethodGraphQL(Enum):
    """GraphQL enum for HttpMethod"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@strawberry.enum
class HookTypeGraphQL(Enum):
    """GraphQL enum for HookType"""
    SHELL = "shell"
    HTTP = "http"
    PYTHON = "python"
    FILE = "file"


@strawberry.enum
class HookTriggerModeGraphQL(Enum):
    """GraphQL enum for HookTriggerMode"""
    NONE = "none"
    MANUAL = "manual"
    HOOK = "hook"


@strawberry.enum
class ConditionTypeGraphQL(Enum):
    """GraphQL enum for ConditionType"""
    DETECT_MAX_ITERATIONS = "detect_max_iterations"
    CHECK_NODES_EXECUTED = "check_nodes_executed"
    CUSTOM = "custom"
    LLM_DECISION = "llm_decision"


@strawberry.enum
class TemplateEngineGraphQL(Enum):
    """GraphQL enum for TemplateEngine"""
    INTERNAL = "internal"
    JINJA2 = "jinja2"


@strawberry.enum
class IRBuilderTargetTypeGraphQL(Enum):
    """GraphQL enum for IRBuilderTargetType"""
    BACKEND = "backend"
    FRONTEND = "frontend"
    STRAWBERRY = "strawberry"
    CUSTOM = "custom"


@strawberry.enum
class IRBuilderSourceTypeGraphQL(Enum):
    """GraphQL enum for IRBuilderSourceType"""
    AST = "ast"
    SCHEMA = "schema"
    CONFIG = "config"
    AUTO = "auto"


@strawberry.enum
class IRBuilderOutputFormatGraphQL(Enum):
    """GraphQL enum for IRBuilderOutputFormat"""
    JSON = "json"
    YAML = "yaml"
    PYTHON = "python"


@strawberry.enum
class TypeScriptExtractPatternGraphQL(Enum):
    """GraphQL enum for TypeScriptExtractPattern"""
    INTERFACE = "interface"
    TYPE = "type"
    ENUM = "enum"
    CLASS = "class"
    FUNCTION = "function"
    CONST = "const"
    EXPORT = "export"


@strawberry.enum
class TypeScriptParseModeGraphQL(Enum):
    """GraphQL enum for TypeScriptParseMode"""
    MODULE = "module"
    SCRIPT = "script"


@strawberry.enum
class TypeScriptOutputFormatGraphQL(Enum):
    """GraphQL enum for TypeScriptOutputFormat"""
    STANDARD = "standard"
    FOR_CODEGEN = "for_codegen"
    FOR_ANALYSIS = "for_analysis"


@strawberry.enum
class DiffFormatGraphQL(Enum):
    """GraphQL enum for DiffFormat"""
    UNIFIED = "unified"
    GIT = "git"
    CONTEXT = "context"
    ED = "ed"
    NORMAL = "normal"


@strawberry.enum
class PatchModeGraphQL(Enum):
    """GraphQL enum for PatchMode"""
    NORMAL = "normal"
    FORCE = "force"
    DRY_RUN = "dry_run"
    REVERSE = "reverse"


@strawberry.enum
class DataFormatGraphQL(Enum):
    """GraphQL enum for DataFormat"""
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"
    TEXT = "text"
    XML = "xml"


@strawberry.enum
class NodeTypeGraphQL(Enum):
    """GraphQL enum for NodeType"""
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


@strawberry.enum
class SeverityGraphQL(Enum):
    """GraphQL enum for Severity"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@strawberry.enum
class EventPriorityGraphQL(Enum):
    """GraphQL enum for EventPriority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"



# Export all GraphQL enums
__all__ = [
    "QueryOperationTypeGraphQL",
    "CrudOperationGraphQL",
    "QueryEntityGraphQL",
    "FieldPresetGraphQL",
    "FieldGroupGraphQL",
    "GraphQLScalarGraphQL",
    "DiPeOBrandedScalarGraphQL",
    "DataTypeGraphQL",
    "ContentTypeGraphQL",
    "HandleDirectionGraphQL",
    "HandleLabelGraphQL",
    "DiagramFormatGraphQL",
    "StatusGraphQL",
    "FlowStatusGraphQL",
    "CompletionStatusGraphQL",
    "ExecutionPhaseGraphQL",
    "EventTypeGraphQL",
    "LLMServiceGraphQL",
    "APIServiceTypeGraphQL",
    "ToolTypeGraphQL",
    "ToolSelectionGraphQL",
    "AuthTypeGraphQL",
    "RetryStrategyGraphQL",
    "DBBlockSubTypeGraphQL",
    "DBOperationGraphQL",
    "SupportedLanguageGraphQL",
    "HttpMethodGraphQL",
    "HookTypeGraphQL",
    "HookTriggerModeGraphQL",
    "ConditionTypeGraphQL",
    "TemplateEngineGraphQL",
    "IRBuilderTargetTypeGraphQL",
    "IRBuilderSourceTypeGraphQL",
    "IRBuilderOutputFormatGraphQL",
    "TypeScriptExtractPatternGraphQL",
    "TypeScriptParseModeGraphQL",
    "TypeScriptOutputFormatGraphQL",
    "DiffFormatGraphQL",
    "PatchModeGraphQL",
    "DataFormatGraphQL",
    "NodeTypeGraphQL",
    "SeverityGraphQL",
    "EventPriorityGraphQL",
]

# Mapping functions for conversion between Python and GraphQL enums

def convert_queryoperationtype_to_graphql(python_enum):
    """Convert Python QueryOperationType enum to GraphQL enum."""
    from ..enums import QueryOperationType
    mapping = {
        QueryOperationType.QUERY: QueryOperationTypeGraphQL.QUERY,
        QueryOperationType.MUTATION: QueryOperationTypeGraphQL.MUTATION,
        QueryOperationType.SUBSCRIPTION: QueryOperationTypeGraphQL.SUBSCRIPTION,
    }
    return mapping.get(python_enum)

def convert_queryoperationtype_from_graphql(graphql_enum):
    """Convert GraphQL QueryOperationType enum to Python enum."""
    from ..enums import QueryOperationType
    mapping = {
        QueryOperationTypeGraphQL.QUERY: QueryOperationType.QUERY,
        QueryOperationTypeGraphQL.MUTATION: QueryOperationType.MUTATION,
        QueryOperationTypeGraphQL.SUBSCRIPTION: QueryOperationType.SUBSCRIPTION,
    }
    return mapping.get(graphql_enum)


def convert_crudoperation_to_graphql(python_enum):
    """Convert Python CrudOperation enum to GraphQL enum."""
    from ..enums import CrudOperation
    mapping = {
        CrudOperation.GET: CrudOperationGraphQL.GET,
        CrudOperation.LIST: CrudOperationGraphQL.LIST,
        CrudOperation.CREATE: CrudOperationGraphQL.CREATE,
        CrudOperation.UPDATE: CrudOperationGraphQL.UPDATE,
        CrudOperation.DELETE: CrudOperationGraphQL.DELETE,
        CrudOperation.SUBSCRIBE: CrudOperationGraphQL.SUBSCRIBE,
    }
    return mapping.get(python_enum)

def convert_crudoperation_from_graphql(graphql_enum):
    """Convert GraphQL CrudOperation enum to Python enum."""
    from ..enums import CrudOperation
    mapping = {
        CrudOperationGraphQL.GET: CrudOperation.GET,
        CrudOperationGraphQL.LIST: CrudOperation.LIST,
        CrudOperationGraphQL.CREATE: CrudOperation.CREATE,
        CrudOperationGraphQL.UPDATE: CrudOperation.UPDATE,
        CrudOperationGraphQL.DELETE: CrudOperation.DELETE,
        CrudOperationGraphQL.SUBSCRIBE: CrudOperation.SUBSCRIBE,
    }
    return mapping.get(graphql_enum)


def convert_queryentity_to_graphql(python_enum):
    """Convert Python QueryEntity enum to GraphQL enum."""
    from ..enums import QueryEntity
    mapping = {
        QueryEntity.DIAGRAM: QueryEntityGraphQL.DIAGRAM,
        QueryEntity.PERSON: QueryEntityGraphQL.PERSON,
        QueryEntity.EXECUTION: QueryEntityGraphQL.EXECUTION,
        QueryEntity.API_KEY: QueryEntityGraphQL.API_KEY,
        QueryEntity.CONVERSATION: QueryEntityGraphQL.CONVERSATION,
        QueryEntity.FILE: QueryEntityGraphQL.FILE,
        QueryEntity.NODE: QueryEntityGraphQL.NODE,
        QueryEntity.PROMPT_TEMPLATE: QueryEntityGraphQL.PROMPT_TEMPLATE,
        QueryEntity.SYSTEM: QueryEntityGraphQL.SYSTEM,
    }
    return mapping.get(python_enum)

def convert_queryentity_from_graphql(graphql_enum):
    """Convert GraphQL QueryEntity enum to Python enum."""
    from ..enums import QueryEntity
    mapping = {
        QueryEntityGraphQL.DIAGRAM: QueryEntity.DIAGRAM,
        QueryEntityGraphQL.PERSON: QueryEntity.PERSON,
        QueryEntityGraphQL.EXECUTION: QueryEntity.EXECUTION,
        QueryEntityGraphQL.API_KEY: QueryEntity.API_KEY,
        QueryEntityGraphQL.CONVERSATION: QueryEntity.CONVERSATION,
        QueryEntityGraphQL.FILE: QueryEntity.FILE,
        QueryEntityGraphQL.NODE: QueryEntity.NODE,
        QueryEntityGraphQL.PROMPT_TEMPLATE: QueryEntity.PROMPT_TEMPLATE,
        QueryEntityGraphQL.SYSTEM: QueryEntity.SYSTEM,
    }
    return mapping.get(graphql_enum)


def convert_fieldpreset_to_graphql(python_enum):
    """Convert Python FieldPreset enum to GraphQL enum."""
    from ..enums import FieldPreset
    mapping = {
        FieldPreset.MINIMAL: FieldPresetGraphQL.MINIMAL,
        FieldPreset.STANDARD: FieldPresetGraphQL.STANDARD,
        FieldPreset.DETAILED: FieldPresetGraphQL.DETAILED,
        FieldPreset.FULL: FieldPresetGraphQL.FULL,
    }
    return mapping.get(python_enum)

def convert_fieldpreset_from_graphql(graphql_enum):
    """Convert GraphQL FieldPreset enum to Python enum."""
    from ..enums import FieldPreset
    mapping = {
        FieldPresetGraphQL.MINIMAL: FieldPreset.MINIMAL,
        FieldPresetGraphQL.STANDARD: FieldPreset.STANDARD,
        FieldPresetGraphQL.DETAILED: FieldPreset.DETAILED,
        FieldPresetGraphQL.FULL: FieldPreset.FULL,
    }
    return mapping.get(graphql_enum)


def convert_fieldgroup_to_graphql(python_enum):
    """Convert Python FieldGroup enum to GraphQL enum."""
    from ..enums import FieldGroup
    mapping = {
        FieldGroup.METADATA: FieldGroupGraphQL.METADATA,
        FieldGroup.TIMESTAMPS: FieldGroupGraphQL.TIMESTAMPS,
        FieldGroup.RELATIONSHIPS: FieldGroupGraphQL.RELATIONSHIPS,
        FieldGroup.CONFIGURATION: FieldGroupGraphQL.CONFIGURATION,
    }
    return mapping.get(python_enum)

def convert_fieldgroup_from_graphql(graphql_enum):
    """Convert GraphQL FieldGroup enum to Python enum."""
    from ..enums import FieldGroup
    mapping = {
        FieldGroupGraphQL.METADATA: FieldGroup.METADATA,
        FieldGroupGraphQL.TIMESTAMPS: FieldGroup.TIMESTAMPS,
        FieldGroupGraphQL.RELATIONSHIPS: FieldGroup.RELATIONSHIPS,
        FieldGroupGraphQL.CONFIGURATION: FieldGroup.CONFIGURATION,
    }
    return mapping.get(graphql_enum)


def convert_graphqlscalar_to_graphql(python_enum):
    """Convert Python GraphQLScalar enum to GraphQL enum."""
    from ..enums import GraphQLScalar
    mapping = {
        GraphQLScalar.ID: GraphQLScalarGraphQL.ID,
        GraphQLScalar.STRING: GraphQLScalarGraphQL.STRING,
        GraphQLScalar.INT: GraphQLScalarGraphQL.INT,
        GraphQLScalar.FLOAT: GraphQLScalarGraphQL.FLOAT,
        GraphQLScalar.BOOLEAN: GraphQLScalarGraphQL.BOOLEAN,
        GraphQLScalar.JSON: GraphQLScalarGraphQL.JSON,
        GraphQLScalar.DATE_TIME: GraphQLScalarGraphQL.DATE_TIME,
        GraphQLScalar.UPLOAD: GraphQLScalarGraphQL.UPLOAD,
    }
    return mapping.get(python_enum)

def convert_graphqlscalar_from_graphql(graphql_enum):
    """Convert GraphQL GraphQLScalar enum to Python enum."""
    from ..enums import GraphQLScalar
    mapping = {
        GraphQLScalarGraphQL.ID: GraphQLScalar.ID,
        GraphQLScalarGraphQL.STRING: GraphQLScalar.STRING,
        GraphQLScalarGraphQL.INT: GraphQLScalar.INT,
        GraphQLScalarGraphQL.FLOAT: GraphQLScalar.FLOAT,
        GraphQLScalarGraphQL.BOOLEAN: GraphQLScalar.BOOLEAN,
        GraphQLScalarGraphQL.JSON: GraphQLScalar.JSON,
        GraphQLScalarGraphQL.DATE_TIME: GraphQLScalar.DATE_TIME,
        GraphQLScalarGraphQL.UPLOAD: GraphQLScalar.UPLOAD,
    }
    return mapping.get(graphql_enum)


def convert_dipeobrandedscalar_to_graphql(python_enum):
    """Convert Python DiPeOBrandedScalar enum to GraphQL enum."""
    from ..enums import DiPeOBrandedScalar
    mapping = {
        DiPeOBrandedScalar.DIAGRAM_ID: DiPeOBrandedScalarGraphQL.DIAGRAM_ID,
        DiPeOBrandedScalar.NODE_ID: DiPeOBrandedScalarGraphQL.NODE_ID,
        DiPeOBrandedScalar.ARROW_ID: DiPeOBrandedScalarGraphQL.ARROW_ID,
        DiPeOBrandedScalar.HANDLE_ID: DiPeOBrandedScalarGraphQL.HANDLE_ID,
        DiPeOBrandedScalar.PERSON_ID: DiPeOBrandedScalarGraphQL.PERSON_ID,
        DiPeOBrandedScalar.API_KEY_ID: DiPeOBrandedScalarGraphQL.API_KEY_ID,
        DiPeOBrandedScalar.EXECUTION_ID: DiPeOBrandedScalarGraphQL.EXECUTION_ID,
        DiPeOBrandedScalar.TASK_ID: DiPeOBrandedScalarGraphQL.TASK_ID,
        DiPeOBrandedScalar.HOOK_ID: DiPeOBrandedScalarGraphQL.HOOK_ID,
    }
    return mapping.get(python_enum)

def convert_dipeobrandedscalar_from_graphql(graphql_enum):
    """Convert GraphQL DiPeOBrandedScalar enum to Python enum."""
    from ..enums import DiPeOBrandedScalar
    mapping = {
        DiPeOBrandedScalarGraphQL.DIAGRAM_ID: DiPeOBrandedScalar.DIAGRAM_ID,
        DiPeOBrandedScalarGraphQL.NODE_ID: DiPeOBrandedScalar.NODE_ID,
        DiPeOBrandedScalarGraphQL.ARROW_ID: DiPeOBrandedScalar.ARROW_ID,
        DiPeOBrandedScalarGraphQL.HANDLE_ID: DiPeOBrandedScalar.HANDLE_ID,
        DiPeOBrandedScalarGraphQL.PERSON_ID: DiPeOBrandedScalar.PERSON_ID,
        DiPeOBrandedScalarGraphQL.API_KEY_ID: DiPeOBrandedScalar.API_KEY_ID,
        DiPeOBrandedScalarGraphQL.EXECUTION_ID: DiPeOBrandedScalar.EXECUTION_ID,
        DiPeOBrandedScalarGraphQL.TASK_ID: DiPeOBrandedScalar.TASK_ID,
        DiPeOBrandedScalarGraphQL.HOOK_ID: DiPeOBrandedScalar.HOOK_ID,
    }
    return mapping.get(graphql_enum)


def convert_datatype_to_graphql(python_enum):
    """Convert Python DataType enum to GraphQL enum."""
    from ..enums import DataType
    mapping = {
        DataType.ANY: DataTypeGraphQL.ANY,
        DataType.STRING: DataTypeGraphQL.STRING,
        DataType.NUMBER: DataTypeGraphQL.NUMBER,
        DataType.BOOLEAN: DataTypeGraphQL.BOOLEAN,
        DataType.OBJECT: DataTypeGraphQL.OBJECT,
        DataType.ARRAY: DataTypeGraphQL.ARRAY,
    }
    return mapping.get(python_enum)

def convert_datatype_from_graphql(graphql_enum):
    """Convert GraphQL DataType enum to Python enum."""
    from ..enums import DataType
    mapping = {
        DataTypeGraphQL.ANY: DataType.ANY,
        DataTypeGraphQL.STRING: DataType.STRING,
        DataTypeGraphQL.NUMBER: DataType.NUMBER,
        DataTypeGraphQL.BOOLEAN: DataType.BOOLEAN,
        DataTypeGraphQL.OBJECT: DataType.OBJECT,
        DataTypeGraphQL.ARRAY: DataType.ARRAY,
    }
    return mapping.get(graphql_enum)


def convert_contenttype_to_graphql(python_enum):
    """Convert Python ContentType enum to GraphQL enum."""
    from ..enums import ContentType
    mapping = {
        ContentType.RAW_TEXT: ContentTypeGraphQL.RAW_TEXT,
        ContentType.CONVERSATION_STATE: ContentTypeGraphQL.CONVERSATION_STATE,
        ContentType.OBJECT: ContentTypeGraphQL.OBJECT,
        ContentType.EMPTY: ContentTypeGraphQL.EMPTY,
        ContentType.GENERIC: ContentTypeGraphQL.GENERIC,
        ContentType.VARIABLE: ContentTypeGraphQL.VARIABLE,
        ContentType.BINARY: ContentTypeGraphQL.BINARY,
    }
    return mapping.get(python_enum)

def convert_contenttype_from_graphql(graphql_enum):
    """Convert GraphQL ContentType enum to Python enum."""
    from ..enums import ContentType
    mapping = {
        ContentTypeGraphQL.RAW_TEXT: ContentType.RAW_TEXT,
        ContentTypeGraphQL.CONVERSATION_STATE: ContentType.CONVERSATION_STATE,
        ContentTypeGraphQL.OBJECT: ContentType.OBJECT,
        ContentTypeGraphQL.EMPTY: ContentType.EMPTY,
        ContentTypeGraphQL.GENERIC: ContentType.GENERIC,
        ContentTypeGraphQL.VARIABLE: ContentType.VARIABLE,
        ContentTypeGraphQL.BINARY: ContentType.BINARY,
    }
    return mapping.get(graphql_enum)


def convert_handledirection_to_graphql(python_enum):
    """Convert Python HandleDirection enum to GraphQL enum."""
    from ..enums import HandleDirection
    mapping = {
        HandleDirection.INPUT: HandleDirectionGraphQL.INPUT,
        HandleDirection.OUTPUT: HandleDirectionGraphQL.OUTPUT,
    }
    return mapping.get(python_enum)

def convert_handledirection_from_graphql(graphql_enum):
    """Convert GraphQL HandleDirection enum to Python enum."""
    from ..enums import HandleDirection
    mapping = {
        HandleDirectionGraphQL.INPUT: HandleDirection.INPUT,
        HandleDirectionGraphQL.OUTPUT: HandleDirection.OUTPUT,
    }
    return mapping.get(graphql_enum)


def convert_handlelabel_to_graphql(python_enum):
    """Convert Python HandleLabel enum to GraphQL enum."""
    from ..enums import HandleLabel
    mapping = {
        HandleLabel.DEFAULT: HandleLabelGraphQL.DEFAULT,
        HandleLabel.FIRST: HandleLabelGraphQL.FIRST,
        HandleLabel.CONDTRUE: HandleLabelGraphQL.CONDTRUE,
        HandleLabel.CONDFALSE: HandleLabelGraphQL.CONDFALSE,
        HandleLabel.SUCCESS: HandleLabelGraphQL.SUCCESS,
        HandleLabel.ERROR: HandleLabelGraphQL.ERROR,
        HandleLabel.RESULTS: HandleLabelGraphQL.RESULTS,
    }
    return mapping.get(python_enum)

def convert_handlelabel_from_graphql(graphql_enum):
    """Convert GraphQL HandleLabel enum to Python enum."""
    from ..enums import HandleLabel
    mapping = {
        HandleLabelGraphQL.DEFAULT: HandleLabel.DEFAULT,
        HandleLabelGraphQL.FIRST: HandleLabel.FIRST,
        HandleLabelGraphQL.CONDTRUE: HandleLabel.CONDTRUE,
        HandleLabelGraphQL.CONDFALSE: HandleLabel.CONDFALSE,
        HandleLabelGraphQL.SUCCESS: HandleLabel.SUCCESS,
        HandleLabelGraphQL.ERROR: HandleLabel.ERROR,
        HandleLabelGraphQL.RESULTS: HandleLabel.RESULTS,
    }
    return mapping.get(graphql_enum)


def convert_diagramformat_to_graphql(python_enum):
    """Convert Python DiagramFormat enum to GraphQL enum."""
    from ..enums import DiagramFormat
    mapping = {
        DiagramFormat.YAML: DiagramFormatGraphQL.YAML,
        DiagramFormat.JSON: DiagramFormatGraphQL.JSON,
        DiagramFormat.LIGHT: DiagramFormatGraphQL.LIGHT,
    }
    return mapping.get(python_enum)

def convert_diagramformat_from_graphql(graphql_enum):
    """Convert GraphQL DiagramFormat enum to Python enum."""
    from ..enums import DiagramFormat
    mapping = {
        DiagramFormatGraphQL.YAML: DiagramFormat.YAML,
        DiagramFormatGraphQL.JSON: DiagramFormat.JSON,
        DiagramFormatGraphQL.LIGHT: DiagramFormat.LIGHT,
    }
    return mapping.get(graphql_enum)


def convert_status_to_graphql(python_enum):
    """Convert Python Status enum to GraphQL enum."""
    from ..enums import Status
    mapping = {
        Status.PENDING: StatusGraphQL.PENDING,
        Status.RUNNING: StatusGraphQL.RUNNING,
        Status.PAUSED: StatusGraphQL.PAUSED,
        Status.COMPLETED: StatusGraphQL.COMPLETED,
        Status.FAILED: StatusGraphQL.FAILED,
        Status.ABORTED: StatusGraphQL.ABORTED,
        Status.SKIPPED: StatusGraphQL.SKIPPED,
        Status.MAXITER_REACHED: StatusGraphQL.MAXITER_REACHED,
    }
    return mapping.get(python_enum)

def convert_status_from_graphql(graphql_enum):
    """Convert GraphQL Status enum to Python enum."""
    from ..enums import Status
    mapping = {
        StatusGraphQL.PENDING: Status.PENDING,
        StatusGraphQL.RUNNING: Status.RUNNING,
        StatusGraphQL.PAUSED: Status.PAUSED,
        StatusGraphQL.COMPLETED: Status.COMPLETED,
        StatusGraphQL.FAILED: Status.FAILED,
        StatusGraphQL.ABORTED: Status.ABORTED,
        StatusGraphQL.SKIPPED: Status.SKIPPED,
        StatusGraphQL.MAXITER_REACHED: Status.MAXITER_REACHED,
    }
    return mapping.get(graphql_enum)


def convert_flowstatus_to_graphql(python_enum):
    """Convert Python FlowStatus enum to GraphQL enum."""
    from ..enums import FlowStatus
    mapping = {
        FlowStatus.WAITING: FlowStatusGraphQL.WAITING,
        FlowStatus.READY: FlowStatusGraphQL.READY,
        FlowStatus.RUNNING: FlowStatusGraphQL.RUNNING,
        FlowStatus.BLOCKED: FlowStatusGraphQL.BLOCKED,
    }
    return mapping.get(python_enum)

def convert_flowstatus_from_graphql(graphql_enum):
    """Convert GraphQL FlowStatus enum to Python enum."""
    from ..enums import FlowStatus
    mapping = {
        FlowStatusGraphQL.WAITING: FlowStatus.WAITING,
        FlowStatusGraphQL.READY: FlowStatus.READY,
        FlowStatusGraphQL.RUNNING: FlowStatus.RUNNING,
        FlowStatusGraphQL.BLOCKED: FlowStatus.BLOCKED,
    }
    return mapping.get(graphql_enum)


def convert_completionstatus_to_graphql(python_enum):
    """Convert Python CompletionStatus enum to GraphQL enum."""
    from ..enums import CompletionStatus
    mapping = {
        CompletionStatus.SUCCESS: CompletionStatusGraphQL.SUCCESS,
        CompletionStatus.FAILED: CompletionStatusGraphQL.FAILED,
        CompletionStatus.SKIPPED: CompletionStatusGraphQL.SKIPPED,
        CompletionStatus.MAX_ITER: CompletionStatusGraphQL.MAX_ITER,
    }
    return mapping.get(python_enum)

def convert_completionstatus_from_graphql(graphql_enum):
    """Convert GraphQL CompletionStatus enum to Python enum."""
    from ..enums import CompletionStatus
    mapping = {
        CompletionStatusGraphQL.SUCCESS: CompletionStatus.SUCCESS,
        CompletionStatusGraphQL.FAILED: CompletionStatus.FAILED,
        CompletionStatusGraphQL.SKIPPED: CompletionStatus.SKIPPED,
        CompletionStatusGraphQL.MAX_ITER: CompletionStatus.MAX_ITER,
    }
    return mapping.get(graphql_enum)


def convert_executionphase_to_graphql(python_enum):
    """Convert Python ExecutionPhase enum to GraphQL enum."""
    from ..enums import ExecutionPhase
    mapping = {
        ExecutionPhase.MEMORY_SELECTION: ExecutionPhaseGraphQL.MEMORY_SELECTION,
        ExecutionPhase.DIRECT_EXECUTION: ExecutionPhaseGraphQL.DIRECT_EXECUTION,
        ExecutionPhase.DECISION_EVALUATION: ExecutionPhaseGraphQL.DECISION_EVALUATION,
        ExecutionPhase.DEFAULT: ExecutionPhaseGraphQL.DEFAULT,
    }
    return mapping.get(python_enum)

def convert_executionphase_from_graphql(graphql_enum):
    """Convert GraphQL ExecutionPhase enum to Python enum."""
    from ..enums import ExecutionPhase
    mapping = {
        ExecutionPhaseGraphQL.MEMORY_SELECTION: ExecutionPhase.MEMORY_SELECTION,
        ExecutionPhaseGraphQL.DIRECT_EXECUTION: ExecutionPhase.DIRECT_EXECUTION,
        ExecutionPhaseGraphQL.DECISION_EVALUATION: ExecutionPhase.DECISION_EVALUATION,
        ExecutionPhaseGraphQL.DEFAULT: ExecutionPhase.DEFAULT,
    }
    return mapping.get(graphql_enum)


def convert_eventtype_to_graphql(python_enum):
    """Convert Python EventType enum to GraphQL enum."""
    from ..enums import EventType
    mapping = {
        EventType.EXECUTION_STARTED: EventTypeGraphQL.EXECUTION_STARTED,
        EventType.EXECUTION_COMPLETED: EventTypeGraphQL.EXECUTION_COMPLETED,
        EventType.EXECUTION_ERROR: EventTypeGraphQL.EXECUTION_ERROR,
        EventType.NODE_STARTED: EventTypeGraphQL.NODE_STARTED,
        EventType.NODE_COMPLETED: EventTypeGraphQL.NODE_COMPLETED,
        EventType.NODE_ERROR: EventTypeGraphQL.NODE_ERROR,
        EventType.NODE_OUTPUT: EventTypeGraphQL.NODE_OUTPUT,
        EventType.EXECUTION_LOG: EventTypeGraphQL.EXECUTION_LOG,
        EventType.INTERACTIVE_PROMPT: EventTypeGraphQL.INTERACTIVE_PROMPT,
        EventType.INTERACTIVE_RESPONSE: EventTypeGraphQL.INTERACTIVE_RESPONSE,
    }
    return mapping.get(python_enum)

def convert_eventtype_from_graphql(graphql_enum):
    """Convert GraphQL EventType enum to Python enum."""
    from ..enums import EventType
    mapping = {
        EventTypeGraphQL.EXECUTION_STARTED: EventType.EXECUTION_STARTED,
        EventTypeGraphQL.EXECUTION_COMPLETED: EventType.EXECUTION_COMPLETED,
        EventTypeGraphQL.EXECUTION_ERROR: EventType.EXECUTION_ERROR,
        EventTypeGraphQL.NODE_STARTED: EventType.NODE_STARTED,
        EventTypeGraphQL.NODE_COMPLETED: EventType.NODE_COMPLETED,
        EventTypeGraphQL.NODE_ERROR: EventType.NODE_ERROR,
        EventTypeGraphQL.NODE_OUTPUT: EventType.NODE_OUTPUT,
        EventTypeGraphQL.EXECUTION_LOG: EventType.EXECUTION_LOG,
        EventTypeGraphQL.INTERACTIVE_PROMPT: EventType.INTERACTIVE_PROMPT,
        EventTypeGraphQL.INTERACTIVE_RESPONSE: EventType.INTERACTIVE_RESPONSE,
    }
    return mapping.get(graphql_enum)


def convert_llmservice_to_graphql(python_enum):
    """Convert Python LLMService enum to GraphQL enum."""
    from ..enums import LLMService
    mapping = {
        LLMService.OPENAI: LLMServiceGraphQL.OPENAI,
        LLMService.ANTHROPIC: LLMServiceGraphQL.ANTHROPIC,
        LLMService.CLAUDE_CODE: LLMServiceGraphQL.CLAUDE_CODE,
        LLMService.CLAUDE_CODE_CUSTOM: LLMServiceGraphQL.CLAUDE_CODE_CUSTOM,
        LLMService.GOOGLE: LLMServiceGraphQL.GOOGLE,
        LLMService.GEMINI: LLMServiceGraphQL.GEMINI,
        LLMService.OLLAMA: LLMServiceGraphQL.OLLAMA,
    }
    return mapping.get(python_enum)

def convert_llmservice_from_graphql(graphql_enum):
    """Convert GraphQL LLMService enum to Python enum."""
    from ..enums import LLMService
    mapping = {
        LLMServiceGraphQL.OPENAI: LLMService.OPENAI,
        LLMServiceGraphQL.ANTHROPIC: LLMService.ANTHROPIC,
        LLMServiceGraphQL.CLAUDE_CODE: LLMService.CLAUDE_CODE,
        LLMServiceGraphQL.CLAUDE_CODE_CUSTOM: LLMService.CLAUDE_CODE_CUSTOM,
        LLMServiceGraphQL.GOOGLE: LLMService.GOOGLE,
        LLMServiceGraphQL.GEMINI: LLMService.GEMINI,
        LLMServiceGraphQL.OLLAMA: LLMService.OLLAMA,
    }
    return mapping.get(graphql_enum)


def convert_apiservicetype_to_graphql(python_enum):
    """Convert Python APIServiceType enum to GraphQL enum."""
    from ..enums import APIServiceType
    mapping = {
        APIServiceType.OPENAI: APIServiceTypeGraphQL.OPENAI,
        APIServiceType.ANTHROPIC: APIServiceTypeGraphQL.ANTHROPIC,
        APIServiceType.GOOGLE: APIServiceTypeGraphQL.GOOGLE,
        APIServiceType.GEMINI: APIServiceTypeGraphQL.GEMINI,
        APIServiceType.OLLAMA: APIServiceTypeGraphQL.OLLAMA,
        APIServiceType.CLAUDE_CODE: APIServiceTypeGraphQL.CLAUDE_CODE,
        APIServiceType.CLAUDE_CODE_CUSTOM: APIServiceTypeGraphQL.CLAUDE_CODE_CUSTOM,
    }
    return mapping.get(python_enum)

def convert_apiservicetype_from_graphql(graphql_enum):
    """Convert GraphQL APIServiceType enum to Python enum."""
    from ..enums import APIServiceType
    mapping = {
        APIServiceTypeGraphQL.OPENAI: APIServiceType.OPENAI,
        APIServiceTypeGraphQL.ANTHROPIC: APIServiceType.ANTHROPIC,
        APIServiceTypeGraphQL.GOOGLE: APIServiceType.GOOGLE,
        APIServiceTypeGraphQL.GEMINI: APIServiceType.GEMINI,
        APIServiceTypeGraphQL.OLLAMA: APIServiceType.OLLAMA,
        APIServiceTypeGraphQL.CLAUDE_CODE: APIServiceType.CLAUDE_CODE,
        APIServiceTypeGraphQL.CLAUDE_CODE_CUSTOM: APIServiceType.CLAUDE_CODE_CUSTOM,
    }
    return mapping.get(graphql_enum)


def convert_tooltype_to_graphql(python_enum):
    """Convert Python ToolType enum to GraphQL enum."""
    from ..enums import ToolType
    mapping = {
        ToolType.WEB_SEARCH: ToolTypeGraphQL.WEB_SEARCH,
        ToolType.WEB_SEARCH_PREVIEW: ToolTypeGraphQL.WEB_SEARCH_PREVIEW,
        ToolType.IMAGE_GENERATION: ToolTypeGraphQL.IMAGE_GENERATION,
    }
    return mapping.get(python_enum)

def convert_tooltype_from_graphql(graphql_enum):
    """Convert GraphQL ToolType enum to Python enum."""
    from ..enums import ToolType
    mapping = {
        ToolTypeGraphQL.WEB_SEARCH: ToolType.WEB_SEARCH,
        ToolTypeGraphQL.WEB_SEARCH_PREVIEW: ToolType.WEB_SEARCH_PREVIEW,
        ToolTypeGraphQL.IMAGE_GENERATION: ToolType.IMAGE_GENERATION,
    }
    return mapping.get(graphql_enum)


def convert_toolselection_to_graphql(python_enum):
    """Convert Python ToolSelection enum to GraphQL enum."""
    from ..enums import ToolSelection
    mapping = {
        ToolSelection.NONE: ToolSelectionGraphQL.NONE,
        ToolSelection.IMAGE: ToolSelectionGraphQL.IMAGE,
        ToolSelection.WEBSEARCH: ToolSelectionGraphQL.WEBSEARCH,
    }
    return mapping.get(python_enum)

def convert_toolselection_from_graphql(graphql_enum):
    """Convert GraphQL ToolSelection enum to Python enum."""
    from ..enums import ToolSelection
    mapping = {
        ToolSelectionGraphQL.NONE: ToolSelection.NONE,
        ToolSelectionGraphQL.IMAGE: ToolSelection.IMAGE,
        ToolSelectionGraphQL.WEBSEARCH: ToolSelection.WEBSEARCH,
    }
    return mapping.get(graphql_enum)


def convert_authtype_to_graphql(python_enum):
    """Convert Python AuthType enum to GraphQL enum."""
    from ..enums import AuthType
    mapping = {
        AuthType.NONE: AuthTypeGraphQL.NONE,
        AuthType.BEARER: AuthTypeGraphQL.BEARER,
        AuthType.BASIC: AuthTypeGraphQL.BASIC,
        AuthType.API_KEY: AuthTypeGraphQL.API_KEY,
    }
    return mapping.get(python_enum)

def convert_authtype_from_graphql(graphql_enum):
    """Convert GraphQL AuthType enum to Python enum."""
    from ..enums import AuthType
    mapping = {
        AuthTypeGraphQL.NONE: AuthType.NONE,
        AuthTypeGraphQL.BEARER: AuthType.BEARER,
        AuthTypeGraphQL.BASIC: AuthType.BASIC,
        AuthTypeGraphQL.API_KEY: AuthType.API_KEY,
    }
    return mapping.get(graphql_enum)


def convert_retrystrategy_to_graphql(python_enum):
    """Convert Python RetryStrategy enum to GraphQL enum."""
    from ..enums import RetryStrategy
    mapping = {
        RetryStrategy.NONE: RetryStrategyGraphQL.NONE,
        RetryStrategy.LINEAR: RetryStrategyGraphQL.LINEAR,
        RetryStrategy.EXPONENTIAL: RetryStrategyGraphQL.EXPONENTIAL,
        RetryStrategy.FIBONACCI: RetryStrategyGraphQL.FIBONACCI,
        RetryStrategy.CONSTANT: RetryStrategyGraphQL.CONSTANT,
        RetryStrategy.EXPONENTIAL_BACKOFF: RetryStrategyGraphQL.EXPONENTIAL_BACKOFF,
        RetryStrategy.LINEAR_BACKOFF: RetryStrategyGraphQL.LINEAR_BACKOFF,
        RetryStrategy.FIXED_DELAY: RetryStrategyGraphQL.FIXED_DELAY,
    }
    return mapping.get(python_enum)

def convert_retrystrategy_from_graphql(graphql_enum):
    """Convert GraphQL RetryStrategy enum to Python enum."""
    from ..enums import RetryStrategy
    mapping = {
        RetryStrategyGraphQL.NONE: RetryStrategy.NONE,
        RetryStrategyGraphQL.LINEAR: RetryStrategy.LINEAR,
        RetryStrategyGraphQL.EXPONENTIAL: RetryStrategy.EXPONENTIAL,
        RetryStrategyGraphQL.FIBONACCI: RetryStrategy.FIBONACCI,
        RetryStrategyGraphQL.CONSTANT: RetryStrategy.CONSTANT,
        RetryStrategyGraphQL.EXPONENTIAL_BACKOFF: RetryStrategy.EXPONENTIAL_BACKOFF,
        RetryStrategyGraphQL.LINEAR_BACKOFF: RetryStrategy.LINEAR_BACKOFF,
        RetryStrategyGraphQL.FIXED_DELAY: RetryStrategy.FIXED_DELAY,
    }
    return mapping.get(graphql_enum)


def convert_dbblocksubtype_to_graphql(python_enum):
    """Convert Python DBBlockSubType enum to GraphQL enum."""
    from ..enums import DBBlockSubType
    mapping = {
        DBBlockSubType.FIXED_PROMPT: DBBlockSubTypeGraphQL.FIXED_PROMPT,
        DBBlockSubType.FILE: DBBlockSubTypeGraphQL.FILE,
        DBBlockSubType.CODE: DBBlockSubTypeGraphQL.CODE,
        DBBlockSubType.API_TOOL: DBBlockSubTypeGraphQL.API_TOOL,
    }
    return mapping.get(python_enum)

def convert_dbblocksubtype_from_graphql(graphql_enum):
    """Convert GraphQL DBBlockSubType enum to Python enum."""
    from ..enums import DBBlockSubType
    mapping = {
        DBBlockSubTypeGraphQL.FIXED_PROMPT: DBBlockSubType.FIXED_PROMPT,
        DBBlockSubTypeGraphQL.FILE: DBBlockSubType.FILE,
        DBBlockSubTypeGraphQL.CODE: DBBlockSubType.CODE,
        DBBlockSubTypeGraphQL.API_TOOL: DBBlockSubType.API_TOOL,
    }
    return mapping.get(graphql_enum)


def convert_dboperation_to_graphql(python_enum):
    """Convert Python DBOperation enum to GraphQL enum."""
    from ..enums import DBOperation
    mapping = {
        DBOperation.PROMPT: DBOperationGraphQL.PROMPT,
        DBOperation.READ: DBOperationGraphQL.READ,
        DBOperation.WRITE: DBOperationGraphQL.WRITE,
        DBOperation.APPEND: DBOperationGraphQL.APPEND,
        DBOperation.UPDATE: DBOperationGraphQL.UPDATE,
    }
    return mapping.get(python_enum)

def convert_dboperation_from_graphql(graphql_enum):
    """Convert GraphQL DBOperation enum to Python enum."""
    from ..enums import DBOperation
    mapping = {
        DBOperationGraphQL.PROMPT: DBOperation.PROMPT,
        DBOperationGraphQL.READ: DBOperation.READ,
        DBOperationGraphQL.WRITE: DBOperation.WRITE,
        DBOperationGraphQL.APPEND: DBOperation.APPEND,
        DBOperationGraphQL.UPDATE: DBOperation.UPDATE,
    }
    return mapping.get(graphql_enum)


def convert_supportedlanguage_to_graphql(python_enum):
    """Convert Python SupportedLanguage enum to GraphQL enum."""
    from ..enums import SupportedLanguage
    mapping = {
        SupportedLanguage.PYTHON: SupportedLanguageGraphQL.PYTHON,
        SupportedLanguage.TYPESCRIPT: SupportedLanguageGraphQL.TYPESCRIPT,
        SupportedLanguage.BASH: SupportedLanguageGraphQL.BASH,
        SupportedLanguage.SHELL: SupportedLanguageGraphQL.SHELL,
    }
    return mapping.get(python_enum)

def convert_supportedlanguage_from_graphql(graphql_enum):
    """Convert GraphQL SupportedLanguage enum to Python enum."""
    from ..enums import SupportedLanguage
    mapping = {
        SupportedLanguageGraphQL.PYTHON: SupportedLanguage.PYTHON,
        SupportedLanguageGraphQL.TYPESCRIPT: SupportedLanguage.TYPESCRIPT,
        SupportedLanguageGraphQL.BASH: SupportedLanguage.BASH,
        SupportedLanguageGraphQL.SHELL: SupportedLanguage.SHELL,
    }
    return mapping.get(graphql_enum)


def convert_httpmethod_to_graphql(python_enum):
    """Convert Python HttpMethod enum to GraphQL enum."""
    from ..enums import HttpMethod
    mapping = {
        HttpMethod.GET: HttpMethodGraphQL.GET,
        HttpMethod.POST: HttpMethodGraphQL.POST,
        HttpMethod.PUT: HttpMethodGraphQL.PUT,
        HttpMethod.DELETE: HttpMethodGraphQL.DELETE,
        HttpMethod.PATCH: HttpMethodGraphQL.PATCH,
    }
    return mapping.get(python_enum)

def convert_httpmethod_from_graphql(graphql_enum):
    """Convert GraphQL HttpMethod enum to Python enum."""
    from ..enums import HttpMethod
    mapping = {
        HttpMethodGraphQL.GET: HttpMethod.GET,
        HttpMethodGraphQL.POST: HttpMethod.POST,
        HttpMethodGraphQL.PUT: HttpMethod.PUT,
        HttpMethodGraphQL.DELETE: HttpMethod.DELETE,
        HttpMethodGraphQL.PATCH: HttpMethod.PATCH,
    }
    return mapping.get(graphql_enum)


def convert_hooktype_to_graphql(python_enum):
    """Convert Python HookType enum to GraphQL enum."""
    from ..enums import HookType
    mapping = {
        HookType.SHELL: HookTypeGraphQL.SHELL,
        HookType.HTTP: HookTypeGraphQL.HTTP,
        HookType.PYTHON: HookTypeGraphQL.PYTHON,
        HookType.FILE: HookTypeGraphQL.FILE,
    }
    return mapping.get(python_enum)

def convert_hooktype_from_graphql(graphql_enum):
    """Convert GraphQL HookType enum to Python enum."""
    from ..enums import HookType
    mapping = {
        HookTypeGraphQL.SHELL: HookType.SHELL,
        HookTypeGraphQL.HTTP: HookType.HTTP,
        HookTypeGraphQL.PYTHON: HookType.PYTHON,
        HookTypeGraphQL.FILE: HookType.FILE,
    }
    return mapping.get(graphql_enum)


def convert_hooktriggermode_to_graphql(python_enum):
    """Convert Python HookTriggerMode enum to GraphQL enum."""
    from ..enums import HookTriggerMode
    mapping = {
        HookTriggerMode.NONE: HookTriggerModeGraphQL.NONE,
        HookTriggerMode.MANUAL: HookTriggerModeGraphQL.MANUAL,
        HookTriggerMode.HOOK: HookTriggerModeGraphQL.HOOK,
    }
    return mapping.get(python_enum)

def convert_hooktriggermode_from_graphql(graphql_enum):
    """Convert GraphQL HookTriggerMode enum to Python enum."""
    from ..enums import HookTriggerMode
    mapping = {
        HookTriggerModeGraphQL.NONE: HookTriggerMode.NONE,
        HookTriggerModeGraphQL.MANUAL: HookTriggerMode.MANUAL,
        HookTriggerModeGraphQL.HOOK: HookTriggerMode.HOOK,
    }
    return mapping.get(graphql_enum)


def convert_conditiontype_to_graphql(python_enum):
    """Convert Python ConditionType enum to GraphQL enum."""
    from ..enums import ConditionType
    mapping = {
        ConditionType.DETECT_MAX_ITERATIONS: ConditionTypeGraphQL.DETECT_MAX_ITERATIONS,
        ConditionType.CHECK_NODES_EXECUTED: ConditionTypeGraphQL.CHECK_NODES_EXECUTED,
        ConditionType.CUSTOM: ConditionTypeGraphQL.CUSTOM,
        ConditionType.LLM_DECISION: ConditionTypeGraphQL.LLM_DECISION,
    }
    return mapping.get(python_enum)

def convert_conditiontype_from_graphql(graphql_enum):
    """Convert GraphQL ConditionType enum to Python enum."""
    from ..enums import ConditionType
    mapping = {
        ConditionTypeGraphQL.DETECT_MAX_ITERATIONS: ConditionType.DETECT_MAX_ITERATIONS,
        ConditionTypeGraphQL.CHECK_NODES_EXECUTED: ConditionType.CHECK_NODES_EXECUTED,
        ConditionTypeGraphQL.CUSTOM: ConditionType.CUSTOM,
        ConditionTypeGraphQL.LLM_DECISION: ConditionType.LLM_DECISION,
    }
    return mapping.get(graphql_enum)


def convert_templateengine_to_graphql(python_enum):
    """Convert Python TemplateEngine enum to GraphQL enum."""
    from ..enums import TemplateEngine
    mapping = {
        TemplateEngine.INTERNAL: TemplateEngineGraphQL.INTERNAL,
        TemplateEngine.JINJA2: TemplateEngineGraphQL.JINJA2,
    }
    return mapping.get(python_enum)

def convert_templateengine_from_graphql(graphql_enum):
    """Convert GraphQL TemplateEngine enum to Python enum."""
    from ..enums import TemplateEngine
    mapping = {
        TemplateEngineGraphQL.INTERNAL: TemplateEngine.INTERNAL,
        TemplateEngineGraphQL.JINJA2: TemplateEngine.JINJA2,
    }
    return mapping.get(graphql_enum)


def convert_irbuildertargettype_to_graphql(python_enum):
    """Convert Python IRBuilderTargetType enum to GraphQL enum."""
    from ..enums import IRBuilderTargetType
    mapping = {
        IRBuilderTargetType.BACKEND: IRBuilderTargetTypeGraphQL.BACKEND,
        IRBuilderTargetType.FRONTEND: IRBuilderTargetTypeGraphQL.FRONTEND,
        IRBuilderTargetType.STRAWBERRY: IRBuilderTargetTypeGraphQL.STRAWBERRY,
        IRBuilderTargetType.CUSTOM: IRBuilderTargetTypeGraphQL.CUSTOM,
    }
    return mapping.get(python_enum)

def convert_irbuildertargettype_from_graphql(graphql_enum):
    """Convert GraphQL IRBuilderTargetType enum to Python enum."""
    from ..enums import IRBuilderTargetType
    mapping = {
        IRBuilderTargetTypeGraphQL.BACKEND: IRBuilderTargetType.BACKEND,
        IRBuilderTargetTypeGraphQL.FRONTEND: IRBuilderTargetType.FRONTEND,
        IRBuilderTargetTypeGraphQL.STRAWBERRY: IRBuilderTargetType.STRAWBERRY,
        IRBuilderTargetTypeGraphQL.CUSTOM: IRBuilderTargetType.CUSTOM,
    }
    return mapping.get(graphql_enum)


def convert_irbuildersourcetype_to_graphql(python_enum):
    """Convert Python IRBuilderSourceType enum to GraphQL enum."""
    from ..enums import IRBuilderSourceType
    mapping = {
        IRBuilderSourceType.AST: IRBuilderSourceTypeGraphQL.AST,
        IRBuilderSourceType.SCHEMA: IRBuilderSourceTypeGraphQL.SCHEMA,
        IRBuilderSourceType.CONFIG: IRBuilderSourceTypeGraphQL.CONFIG,
        IRBuilderSourceType.AUTO: IRBuilderSourceTypeGraphQL.AUTO,
    }
    return mapping.get(python_enum)

def convert_irbuildersourcetype_from_graphql(graphql_enum):
    """Convert GraphQL IRBuilderSourceType enum to Python enum."""
    from ..enums import IRBuilderSourceType
    mapping = {
        IRBuilderSourceTypeGraphQL.AST: IRBuilderSourceType.AST,
        IRBuilderSourceTypeGraphQL.SCHEMA: IRBuilderSourceType.SCHEMA,
        IRBuilderSourceTypeGraphQL.CONFIG: IRBuilderSourceType.CONFIG,
        IRBuilderSourceTypeGraphQL.AUTO: IRBuilderSourceType.AUTO,
    }
    return mapping.get(graphql_enum)


def convert_irbuilderoutputformat_to_graphql(python_enum):
    """Convert Python IRBuilderOutputFormat enum to GraphQL enum."""
    from ..enums import IRBuilderOutputFormat
    mapping = {
        IRBuilderOutputFormat.JSON: IRBuilderOutputFormatGraphQL.JSON,
        IRBuilderOutputFormat.YAML: IRBuilderOutputFormatGraphQL.YAML,
        IRBuilderOutputFormat.PYTHON: IRBuilderOutputFormatGraphQL.PYTHON,
    }
    return mapping.get(python_enum)

def convert_irbuilderoutputformat_from_graphql(graphql_enum):
    """Convert GraphQL IRBuilderOutputFormat enum to Python enum."""
    from ..enums import IRBuilderOutputFormat
    mapping = {
        IRBuilderOutputFormatGraphQL.JSON: IRBuilderOutputFormat.JSON,
        IRBuilderOutputFormatGraphQL.YAML: IRBuilderOutputFormat.YAML,
        IRBuilderOutputFormatGraphQL.PYTHON: IRBuilderOutputFormat.PYTHON,
    }
    return mapping.get(graphql_enum)


def convert_typescriptextractpattern_to_graphql(python_enum):
    """Convert Python TypeScriptExtractPattern enum to GraphQL enum."""
    from ..enums import TypeScriptExtractPattern
    mapping = {
        TypeScriptExtractPattern.INTERFACE: TypeScriptExtractPatternGraphQL.INTERFACE,
        TypeScriptExtractPattern.TYPE: TypeScriptExtractPatternGraphQL.TYPE,
        TypeScriptExtractPattern.ENUM: TypeScriptExtractPatternGraphQL.ENUM,
        TypeScriptExtractPattern.CLASS: TypeScriptExtractPatternGraphQL.CLASS,
        TypeScriptExtractPattern.FUNCTION: TypeScriptExtractPatternGraphQL.FUNCTION,
        TypeScriptExtractPattern.CONST: TypeScriptExtractPatternGraphQL.CONST,
        TypeScriptExtractPattern.EXPORT: TypeScriptExtractPatternGraphQL.EXPORT,
    }
    return mapping.get(python_enum)

def convert_typescriptextractpattern_from_graphql(graphql_enum):
    """Convert GraphQL TypeScriptExtractPattern enum to Python enum."""
    from ..enums import TypeScriptExtractPattern
    mapping = {
        TypeScriptExtractPatternGraphQL.INTERFACE: TypeScriptExtractPattern.INTERFACE,
        TypeScriptExtractPatternGraphQL.TYPE: TypeScriptExtractPattern.TYPE,
        TypeScriptExtractPatternGraphQL.ENUM: TypeScriptExtractPattern.ENUM,
        TypeScriptExtractPatternGraphQL.CLASS: TypeScriptExtractPattern.CLASS,
        TypeScriptExtractPatternGraphQL.FUNCTION: TypeScriptExtractPattern.FUNCTION,
        TypeScriptExtractPatternGraphQL.CONST: TypeScriptExtractPattern.CONST,
        TypeScriptExtractPatternGraphQL.EXPORT: TypeScriptExtractPattern.EXPORT,
    }
    return mapping.get(graphql_enum)


def convert_typescriptparsemode_to_graphql(python_enum):
    """Convert Python TypeScriptParseMode enum to GraphQL enum."""
    from ..enums import TypeScriptParseMode
    mapping = {
        TypeScriptParseMode.MODULE: TypeScriptParseModeGraphQL.MODULE,
        TypeScriptParseMode.SCRIPT: TypeScriptParseModeGraphQL.SCRIPT,
    }
    return mapping.get(python_enum)

def convert_typescriptparsemode_from_graphql(graphql_enum):
    """Convert GraphQL TypeScriptParseMode enum to Python enum."""
    from ..enums import TypeScriptParseMode
    mapping = {
        TypeScriptParseModeGraphQL.MODULE: TypeScriptParseMode.MODULE,
        TypeScriptParseModeGraphQL.SCRIPT: TypeScriptParseMode.SCRIPT,
    }
    return mapping.get(graphql_enum)


def convert_typescriptoutputformat_to_graphql(python_enum):
    """Convert Python TypeScriptOutputFormat enum to GraphQL enum."""
    from ..enums import TypeScriptOutputFormat
    mapping = {
        TypeScriptOutputFormat.STANDARD: TypeScriptOutputFormatGraphQL.STANDARD,
        TypeScriptOutputFormat.FOR_CODEGEN: TypeScriptOutputFormatGraphQL.FOR_CODEGEN,
        TypeScriptOutputFormat.FOR_ANALYSIS: TypeScriptOutputFormatGraphQL.FOR_ANALYSIS,
    }
    return mapping.get(python_enum)

def convert_typescriptoutputformat_from_graphql(graphql_enum):
    """Convert GraphQL TypeScriptOutputFormat enum to Python enum."""
    from ..enums import TypeScriptOutputFormat
    mapping = {
        TypeScriptOutputFormatGraphQL.STANDARD: TypeScriptOutputFormat.STANDARD,
        TypeScriptOutputFormatGraphQL.FOR_CODEGEN: TypeScriptOutputFormat.FOR_CODEGEN,
        TypeScriptOutputFormatGraphQL.FOR_ANALYSIS: TypeScriptOutputFormat.FOR_ANALYSIS,
    }
    return mapping.get(graphql_enum)


def convert_diffformat_to_graphql(python_enum):
    """Convert Python DiffFormat enum to GraphQL enum."""
    from ..enums import DiffFormat
    mapping = {
        DiffFormat.UNIFIED: DiffFormatGraphQL.UNIFIED,
        DiffFormat.GIT: DiffFormatGraphQL.GIT,
        DiffFormat.CONTEXT: DiffFormatGraphQL.CONTEXT,
        DiffFormat.ED: DiffFormatGraphQL.ED,
        DiffFormat.NORMAL: DiffFormatGraphQL.NORMAL,
    }
    return mapping.get(python_enum)

def convert_diffformat_from_graphql(graphql_enum):
    """Convert GraphQL DiffFormat enum to Python enum."""
    from ..enums import DiffFormat
    mapping = {
        DiffFormatGraphQL.UNIFIED: DiffFormat.UNIFIED,
        DiffFormatGraphQL.GIT: DiffFormat.GIT,
        DiffFormatGraphQL.CONTEXT: DiffFormat.CONTEXT,
        DiffFormatGraphQL.ED: DiffFormat.ED,
        DiffFormatGraphQL.NORMAL: DiffFormat.NORMAL,
    }
    return mapping.get(graphql_enum)


def convert_patchmode_to_graphql(python_enum):
    """Convert Python PatchMode enum to GraphQL enum."""
    from ..enums import PatchMode
    mapping = {
        PatchMode.NORMAL: PatchModeGraphQL.NORMAL,
        PatchMode.FORCE: PatchModeGraphQL.FORCE,
        PatchMode.DRY_RUN: PatchModeGraphQL.DRY_RUN,
        PatchMode.REVERSE: PatchModeGraphQL.REVERSE,
    }
    return mapping.get(python_enum)

def convert_patchmode_from_graphql(graphql_enum):
    """Convert GraphQL PatchMode enum to Python enum."""
    from ..enums import PatchMode
    mapping = {
        PatchModeGraphQL.NORMAL: PatchMode.NORMAL,
        PatchModeGraphQL.FORCE: PatchMode.FORCE,
        PatchModeGraphQL.DRY_RUN: PatchMode.DRY_RUN,
        PatchModeGraphQL.REVERSE: PatchMode.REVERSE,
    }
    return mapping.get(graphql_enum)


def convert_dataformat_to_graphql(python_enum):
    """Convert Python DataFormat enum to GraphQL enum."""
    from ..enums import DataFormat
    mapping = {
        DataFormat.JSON: DataFormatGraphQL.JSON,
        DataFormat.YAML: DataFormatGraphQL.YAML,
        DataFormat.CSV: DataFormatGraphQL.CSV,
        DataFormat.TEXT: DataFormatGraphQL.TEXT,
        DataFormat.XML: DataFormatGraphQL.XML,
    }
    return mapping.get(python_enum)

def convert_dataformat_from_graphql(graphql_enum):
    """Convert GraphQL DataFormat enum to Python enum."""
    from ..enums import DataFormat
    mapping = {
        DataFormatGraphQL.JSON: DataFormat.JSON,
        DataFormatGraphQL.YAML: DataFormat.YAML,
        DataFormatGraphQL.CSV: DataFormat.CSV,
        DataFormatGraphQL.TEXT: DataFormat.TEXT,
        DataFormatGraphQL.XML: DataFormat.XML,
    }
    return mapping.get(graphql_enum)


def convert_nodetype_to_graphql(python_enum):
    """Convert Python NodeType enum to GraphQL enum."""
    from ..enums import NodeType
    mapping = {
        NodeType.START: NodeTypeGraphQL.START,
        NodeType.PERSON_JOB: NodeTypeGraphQL.PERSON_JOB,
        NodeType.CONDITION: NodeTypeGraphQL.CONDITION,
        NodeType.CODE_JOB: NodeTypeGraphQL.CODE_JOB,
        NodeType.API_JOB: NodeTypeGraphQL.API_JOB,
        NodeType.ENDPOINT: NodeTypeGraphQL.ENDPOINT,
        NodeType.DB: NodeTypeGraphQL.DB,
        NodeType.USER_RESPONSE: NodeTypeGraphQL.USER_RESPONSE,
        NodeType.HOOK: NodeTypeGraphQL.HOOK,
        NodeType.TEMPLATE_JOB: NodeTypeGraphQL.TEMPLATE_JOB,
        NodeType.JSON_SCHEMA_VALIDATOR: NodeTypeGraphQL.JSON_SCHEMA_VALIDATOR,
        NodeType.TYPESCRIPT_AST: NodeTypeGraphQL.TYPESCRIPT_AST,
        NodeType.SUB_DIAGRAM: NodeTypeGraphQL.SUB_DIAGRAM,
        NodeType.INTEGRATED_API: NodeTypeGraphQL.INTEGRATED_API,
        NodeType.IR_BUILDER: NodeTypeGraphQL.IR_BUILDER,
        NodeType.DIFF_PATCH: NodeTypeGraphQL.DIFF_PATCH,
    }
    return mapping.get(python_enum)

def convert_nodetype_from_graphql(graphql_enum):
    """Convert GraphQL NodeType enum to Python enum."""
    from ..enums import NodeType
    mapping = {
        NodeTypeGraphQL.START: NodeType.START,
        NodeTypeGraphQL.PERSON_JOB: NodeType.PERSON_JOB,
        NodeTypeGraphQL.CONDITION: NodeType.CONDITION,
        NodeTypeGraphQL.CODE_JOB: NodeType.CODE_JOB,
        NodeTypeGraphQL.API_JOB: NodeType.API_JOB,
        NodeTypeGraphQL.ENDPOINT: NodeType.ENDPOINT,
        NodeTypeGraphQL.DB: NodeType.DB,
        NodeTypeGraphQL.USER_RESPONSE: NodeType.USER_RESPONSE,
        NodeTypeGraphQL.HOOK: NodeType.HOOK,
        NodeTypeGraphQL.TEMPLATE_JOB: NodeType.TEMPLATE_JOB,
        NodeTypeGraphQL.JSON_SCHEMA_VALIDATOR: NodeType.JSON_SCHEMA_VALIDATOR,
        NodeTypeGraphQL.TYPESCRIPT_AST: NodeType.TYPESCRIPT_AST,
        NodeTypeGraphQL.SUB_DIAGRAM: NodeType.SUB_DIAGRAM,
        NodeTypeGraphQL.INTEGRATED_API: NodeType.INTEGRATED_API,
        NodeTypeGraphQL.IR_BUILDER: NodeType.IR_BUILDER,
        NodeTypeGraphQL.DIFF_PATCH: NodeType.DIFF_PATCH,
    }
    return mapping.get(graphql_enum)


def convert_severity_to_graphql(python_enum):
    """Convert Python Severity enum to GraphQL enum."""
    from ..enums import Severity
    mapping = {
        Severity.ERROR: SeverityGraphQL.ERROR,
        Severity.WARNING: SeverityGraphQL.WARNING,
        Severity.INFO: SeverityGraphQL.INFO,
    }
    return mapping.get(python_enum)

def convert_severity_from_graphql(graphql_enum):
    """Convert GraphQL Severity enum to Python enum."""
    from ..enums import Severity
    mapping = {
        SeverityGraphQL.ERROR: Severity.ERROR,
        SeverityGraphQL.WARNING: Severity.WARNING,
        SeverityGraphQL.INFO: Severity.INFO,
    }
    return mapping.get(graphql_enum)


def convert_eventpriority_to_graphql(python_enum):
    """Convert Python EventPriority enum to GraphQL enum."""
    from ..enums import EventPriority
    mapping = {
        EventPriority.LOW: EventPriorityGraphQL.LOW,
        EventPriority.NORMAL: EventPriorityGraphQL.NORMAL,
        EventPriority.HIGH: EventPriorityGraphQL.HIGH,
        EventPriority.CRITICAL: EventPriorityGraphQL.CRITICAL,
    }
    return mapping.get(python_enum)

def convert_eventpriority_from_graphql(graphql_enum):
    """Convert GraphQL EventPriority enum to Python enum."""
    from ..enums import EventPriority
    mapping = {
        EventPriorityGraphQL.LOW: EventPriority.LOW,
        EventPriorityGraphQL.NORMAL: EventPriority.NORMAL,
        EventPriorityGraphQL.HIGH: EventPriority.HIGH,
        EventPriorityGraphQL.CRITICAL: EventPriority.CRITICAL,
    }
    return mapping.get(graphql_enum)


