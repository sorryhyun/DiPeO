"""Generated code for DiPeO diagram system."""

# Re-export enums
from .enums import (
    NodeType,
    NodeExecutionStatus,
    LLMService,
    ContentType,
    DataType,
    HandleDirection,
    HandleLabel,
    MemoryView,
    DiagramFormat,
    DBBlockSubType,
    SupportedLanguage,
    HttpMethod,
    HookType,
    HookTriggerMode,
    ExecutionStatus,
    EventType,
    APIServiceType,
    NotionOperation,
    ToolType,
)

# Re-export all domain models
from .domain_models import (
    # Core types
    NodeID,
    HandleID,
    ApiKeyID,

    # Domain models
    Vec2,
    DomainHandle,
    DomainNode,
    DomainArrow,
    DomainPerson,
    DomainApiKey,
    DomainDiagram,
    DiagramMetadata,

    # Execution models
    NodeState,
    ExecutionState,
    ExecutionOptions,
    TokenUsage,

    # Configuration models
    MemorySettings,
    PersonLLMConfig,

    # Other models
    BaseNodeData,
    InteractivePromptData,
    InteractiveResponse,
    ExecutionUpdate,
    NodeDefinition,
    Message,
    ConversationMetadata,
    Conversation,
    ValidationRules,
    UIConfiguration,
    FieldSpecification,
    HandleConfiguration,
    OutputSpecification,
    ExecutionConfiguration,
    ExampleConfiguration,
    NodeSpecification,
    NodeSpecificationRegistry,
    ToolConfig,
    WebSearchResult,
    ImageGenerationResult,
    ToolOutput,
    ChatResult,
    LLMRequestOptions,
)

# Re-export functions from handle_utils
from .handle_utils import (
    create_handle_id,
    parse_handle_id,
    parse_handle_id_safe,
    extract_node_id_from_handle,
    is_valid_handle_id,
)

# Re-export functions from conversions
from .conversions import (
    node_kind_to_domain_type,
    domain_type_to_node_kind,
    normalize_node_id,
    diagram_arrays_to_maps,
    diagram_maps_to_arrays,
)

__all__ = [
    # Core types
    "NodeID",
    "HandleID",
    "ApiKeyID",

    # Enums
    "NodeType",
    "NodeExecutionStatus",
    "LLMService",
    "ContentType",
    "DataType",
    "HandleDirection",
    "HandleLabel",
    "MemoryView",
    "DiagramFormat",
    "DBBlockSubType",
    "SupportedLanguage",
    "HttpMethod",
    "HookType",
    "HookTriggerMode",
    "ExecutionStatus",
    "EventType",
    "APIServiceType",
    "NotionOperation",
    "ToolType",

    # Domain models
    "Vec2",
    "DomainHandle",
    "DomainNode",
    "DomainArrow",
    "DomainPerson",
    "DomainApiKey",
    "DomainDiagram",
    "DiagramMetadata",

    # Execution models
    "NodeState",
    "ExecutionState",
    "ExecutionOptions",
    "TokenUsage",

    # Configuration models
    "MemorySettings",
    "PersonLLMConfig",

    # Other models
    "BaseNodeData",
    "InteractivePromptData",
    "InteractiveResponse",
    "ExecutionUpdate",
    "NodeDefinition",
    "Message",
    "ConversationMetadata",
    "Conversation",
    "ValidationRules",
    "UIConfiguration",
    "FieldSpecification",
    "HandleConfiguration",
    "OutputSpecification",
    "ExecutionConfiguration",
    "ExampleConfiguration",
    "NodeSpecification",
    "NodeSpecificationRegistry",
    "ToolConfig",
    "WebSearchResult",
    "ImageGenerationResult",
    "ToolOutput",
    "ChatResult",
    "LLMRequestOptions",

    # Functions from handle_utils
    "create_handle_id",
    "parse_handle_id",
    "parse_handle_id_safe",
    "extract_node_id_from_handle",
    "is_valid_handle_id",

    # Functions from conversions
    "node_kind_to_domain_type",
    "domain_type_to_node_kind",
    "normalize_node_id",
    "diagram_arrays_to_maps",
    "diagram_maps_to_arrays",
]
