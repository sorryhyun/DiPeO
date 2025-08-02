"""DiPeO models package - Compatibility layer for migration to diagram_generated.

This package now redirects to the new diagram-generated models.
Legacy imports from dipeo.models will continue to work during migration.
"""

# Redirect imports to new diagram_generated module
from dipeo.diagram_generated.conversions import *
from dipeo.diagram_generated.handle_utils import *
from dipeo.diagram_generated.domain_models import *
from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *

# For backward compatibility, also import from legacy models if needed
# This will be removed in Phase 5
try:
    from .models import *
except ImportError:
    # Legacy models may not exist, that's okay
    pass

# Combine all exports from submodules
__all__ = [
    # From models.py
    "APIServiceType", "ApiJobNodeData", "ApiKeyID", "ArrowID",
    "BaseNodeData", "ChatResult", "CodeJobNodeData", "ConditionNodeData",
    "ConfigDict", "ContentType", "Conversation", "ConversationMetadata",
    "DBBlockSubType", "DBNodeData", "DataType", "DiagramFormat",
    "DiagramID", "DiagramMetadata", "DomainApiKey", "DomainArrow",
    "DomainDiagram", "DomainHandle", "DomainNode", "DomainPerson",
    "EndpointNodeData", "EventType", "ExecutionID", "ExecutionOptions",
    "ExecutionState", "ExecutionStatus", "ExecutionUpdate", "ForgettingMode",
    "HandleDirection", "HandleID", "HandleLabel",
    "HookNodeData", "HookTriggerMode", "HookType", "HttpMethod",
    "ImageGenerationResult", "InteractivePromptData", "InteractiveResponse",
    "LLMRequestOptions", "LLMService", "MemorySettings",
    "Message", "NewType", "NodeDefinition", "NodeExecutionStatus",
    "NodeID", "NodeState", "NodeType",
    "NotionNodeData", "NotionOperation", "PersonBatchJobNodeData", "PersonID",
    "PersonJobNodeData", "PersonLLMConfig", "PersonMemoryMessage",
    "StartNodeData", "SupportedLanguage",
    "TokenUsage", "ToolConfig", "ToolOutput", "ToolType",
    "UserResponseNodeData", "Vec2", "WebSearchResult",
    # From conversions.py
    "NODE_TYPE_MAP", "NODE_TYPE_REVERSE_MAP", "node_kind_to_domain_type",
    "domain_type_to_node_kind", "normalize_node_id", "create_handle_id",
    "parse_handle_id", "diagram_arrays_to_maps", "diagram_maps_to_arrays",
    # From handle_utils.py
    "ParsedHandle", "HandleReference", "parse_handle_id_safe",
    "extract_node_id_from_handle", "is_valid_handle_id",
]