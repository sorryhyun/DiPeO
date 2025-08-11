"""Generated code for DiPeO diagram system."""

# Re-export enums
from .enums import (
    NodeType,
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
    EventType,
    APIServiceType,
    ToolType,
    Status
)
# Re-export all domain models
from .domain_models import (
    # Core types
    NodeID,
    HandleID,
    ApiKeyID,
    PersonID,
    DiagramID,
    ExecutionID,
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
    SerializedNodeOutput,
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
    ToolConfig,
    WebSearchResult,
    ImageGenerationResult,
    ToolOutput,
    ChatResult,
    LLMRequestOptions,
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
    "PersonID",
    "DiagramID",
    "ExecutionID",
    # Enums
    "NodeType",
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
    "EventType",
    "APIServiceType",
    "ToolType",
    "Status",

    # Domain models
    "Vec2",
    "DomainHandle",
    "DomainNode",
    "DomainArrow",
    "DomainPerson",
    "DomainApiKey",
    "DomainDiagram",
    "SerializedNodeOutput",
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
    "ToolConfig",
    "WebSearchResult",
    "ImageGenerationResult",
    "ToolOutput",
    "ChatResult",
    "LLMRequestOptions",

    # Functions from conversions
    "node_kind_to_domain_type",
    "domain_type_to_node_kind",
    "normalize_node_id",
    "diagram_arrays_to_maps",
    "diagram_maps_to_arrays",
]
