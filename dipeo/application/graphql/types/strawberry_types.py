"""
Strawberry GraphQL types for DiPeO application layer.

This module defines Strawberry types directly from Pydantic domain models
using Strawberry's built-in Pydantic integration.
"""

from typing import Optional, List, Dict, Any
import strawberry
from strawberry.scalars import JSON as JSONScalar

# Import the Pydantic models
from dipeo.diagram_generated.domain_models import (
    DomainDiagram,
    DomainNode,
    DomainHandle,
    DomainArrow,
    DomainPerson,
    DomainApiKey,
    ExecutionState,
    NodeState,
    TokenUsage,
    DiagramMetadata,
    PersonLLMConfig,
    MemorySettings,
    Vec2,
    ExecutionOptions,
    InteractivePromptData,
    InteractiveResponse,
    NodeDefinition,
    Message,
    ConversationMetadata,
    Conversation,
    # Import ID types
    NodeID,
    HandleID,
    ArrowID,
    PersonID,
    ApiKeyID,
    DiagramID,
    ExecutionID,
    HookID,
    TaskID,
)

# Import enums
from dipeo.diagram_generated.enums import (
    NodeType, HandleDirection, HandleLabel, DataType, MemoryView,
    DiagramFormat, DBBlockSubType, ContentType, SupportedLanguage,
    HttpMethod, HookType, HookTriggerMode, ExecutionStatus,
    NodeExecutionStatus, EventType, LLMService, APIServiceType,
    NotionOperation, ToolType
)

# Register scalar types
NodeIDScalar = strawberry.scalar(
    NodeID,
    name="NodeID",
    description="Unique identifier for nodes",
    serialize=lambda v: str(v),
    parse_value=lambda v: NodeID(v) if v else None,
)

HandleIDScalar = strawberry.scalar(
    HandleID,
    name="HandleID",
    description="Unique identifier for handles",
    serialize=lambda v: str(v),
    parse_value=lambda v: HandleID(v) if v else None,
)

ArrowIDScalar = strawberry.scalar(
    ArrowID,
    name="ArrowID",
    description="Unique identifier for arrows",
    serialize=lambda v: str(v),
    parse_value=lambda v: ArrowID(v) if v else None,
)

PersonIDScalar = strawberry.scalar(
    PersonID,
    name="PersonID",
    description="Unique identifier for persons",
    serialize=lambda v: str(v),
    parse_value=lambda v: PersonID(v) if v else None,
)

ApiKeyIDScalar = strawberry.scalar(
    ApiKeyID,
    name="ApiKeyID",
    description="Unique identifier for API keys",
    serialize=lambda v: str(v),
    parse_value=lambda v: ApiKeyID(v) if v else None,
)

DiagramIDScalar = strawberry.scalar(
    DiagramID,
    name="DiagramID",
    description="Unique identifier for diagrams",
    serialize=lambda v: str(v),
    parse_value=lambda v: DiagramID(v) if v else None,
)

ExecutionIDScalar = strawberry.scalar(
    ExecutionID,
    name="ExecutionID",
    description="Unique identifier for executions",
    serialize=lambda v: str(v),
    parse_value=lambda v: ExecutionID(v) if v else None,
)

HookIDScalar = strawberry.scalar(
    HookID,
    name="HookID",
    description="Unique identifier for hooks",
    serialize=lambda v: str(v),
    parse_value=lambda v: HookID(v) if v else None,
)

TaskIDScalar = strawberry.scalar(
    TaskID,
    name="TaskID",
    description="Unique identifier for tasks",
    serialize=lambda v: str(v),
    parse_value=lambda v: TaskID(v) if v else None,
)

# Register enums
NodeTypeEnum = strawberry.enum(NodeType, name="NodeType")
HandleDirectionEnum = strawberry.enum(HandleDirection, name="HandleDirection")
HandleLabelEnum = strawberry.enum(HandleLabel, name="HandleLabel")
DataTypeEnum = strawberry.enum(DataType, name="DataType")
MemoryViewEnum = strawberry.enum(MemoryView, name="MemoryView")
DiagramFormatEnum = strawberry.enum(DiagramFormat, name="DiagramFormat")
DBBlockSubTypeEnum = strawberry.enum(DBBlockSubType, name="DBBlockSubType")
ContentTypeEnum = strawberry.enum(ContentType, name="ContentType")
SupportedLanguageEnum = strawberry.enum(SupportedLanguage, name="SupportedLanguage")
HttpMethodEnum = strawberry.enum(HttpMethod, name="HttpMethod")
HookTypeEnum = strawberry.enum(HookType, name="HookType")
HookTriggerModeEnum = strawberry.enum(HookTriggerMode, name="HookTriggerMode")
ExecutionStatusEnum = strawberry.enum(ExecutionStatus, name="ExecutionStatus")
NodeExecutionStatusEnum = strawberry.enum(NodeExecutionStatus, name="NodeExecutionStatus")
EventTypeEnum = strawberry.enum(EventType, name="EventType")
LLMServiceEnum = strawberry.enum(LLMService, name="LLMService")
APIServiceTypeEnum = strawberry.enum(APIServiceType, name="APIServiceType")
NotionOperationEnum = strawberry.enum(NotionOperation, name="NotionOperation")
ToolTypeEnum = strawberry.enum(ToolType, name="ToolType")

# Create Strawberry types from Pydantic models

@strawberry.experimental.pydantic.type(model=Vec2, all_fields=True)
class Vec2Type:
    pass

@strawberry.experimental.pydantic.type(model=TokenUsage, all_fields=True)
class TokenUsageType:
    pass

@strawberry.experimental.pydantic.type(model=NodeState, all_fields=True)
class NodeStateType:
    pass

@strawberry.experimental.pydantic.type(model=DomainHandle, all_fields=True)
class DomainHandleType:
    @strawberry.field
    def id(self) -> HandleID:
        return HandleID(str(self.id))
    
    @strawberry.field
    def node_id(self) -> NodeID:
        return NodeID(str(self.node_id))

@strawberry.experimental.pydantic.type(model=DomainNode, all_fields=True)
class DomainNodeType:
    @strawberry.field
    def id(self) -> NodeID:
        return NodeID(str(self.id))
    
    @strawberry.field
    def data(self) -> JSONScalar:
        # Return the data field as JSON
        return self.data if hasattr(self, 'data') else {}

@strawberry.experimental.pydantic.type(model=DomainArrow, all_fields=True)
class DomainArrowType:
    @strawberry.field
    def id(self) -> ArrowID:
        return ArrowID(str(self.id))
    
    @strawberry.field
    def source(self) -> HandleID:
        return HandleID(str(self.source))
    
    @strawberry.field
    def target(self) -> HandleID:
        return HandleID(str(self.target))
    
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        return self.data if hasattr(self, 'data') else None

@strawberry.experimental.pydantic.type(model=PersonLLMConfig, all_fields=True)
class PersonLLMConfigType:
    pass

@strawberry.experimental.pydantic.type(model=MemorySettings, all_fields=True) 
class MemorySettingsType:
    pass

@strawberry.experimental.pydantic.type(model=DomainPerson, all_fields=True)
class DomainPersonType:
    @strawberry.field
    def id(self) -> PersonID:
        return PersonID(str(self.id))
    
    @strawberry.field
    def type(self) -> str:
        return "person"

@strawberry.experimental.pydantic.type(model=DomainApiKey, all_fields=True)
class DomainApiKeyType:
    @strawberry.field
    def id(self) -> ApiKeyID:
        return ApiKeyID(str(self.id))

@strawberry.experimental.pydantic.type(model=DiagramMetadata, all_fields=True)
class DiagramMetadataType:
    pass

@strawberry.experimental.pydantic.type(model=DomainDiagram, all_fields=True)
class DomainDiagramType:
    @strawberry.field
    def node_count(self) -> int:
        return len(self.nodes) if hasattr(self, 'nodes') else 0
    
    @strawberry.field
    def arrow_count(self) -> int:
        return len(self.arrows) if hasattr(self, 'arrows') else 0

@strawberry.experimental.pydantic.type(model=ExecutionOptions, all_fields=True)
class ExecutionOptionsType:
    @strawberry.field
    def mode(self) -> Optional[str]:
        return self.mode if hasattr(self, 'mode') else None
    
    @strawberry.field
    def variables(self) -> JSONScalar:
        return self.variables if hasattr(self, 'variables') else {}

@strawberry.experimental.pydantic.type(model=ExecutionState, all_fields=True)
class ExecutionStateType:
    @strawberry.field
    def node_states(self) -> JSONScalar:
        if hasattr(self, 'node_states') and self.node_states:
            # Convert NodeState objects to dicts
            return {k: v.model_dump() if hasattr(v, 'model_dump') else v 
                    for k, v in self.node_states.items()}
        return {}
    
    @strawberry.field
    def node_outputs(self) -> JSONScalar:
        return self.node_outputs if hasattr(self, 'node_outputs') else {}
    
    @strawberry.field
    def variables(self) -> JSONScalar:
        return self.variables if hasattr(self, 'variables') else {}
    
    @strawberry.field
    def exec_counts(self) -> JSONScalar:
        return self.exec_counts if hasattr(self, 'exec_counts') else {}

@strawberry.experimental.pydantic.type(model=InteractivePromptData, all_fields=True)
class InteractivePromptDataType:
    pass

@strawberry.experimental.pydantic.type(model=InteractiveResponse, all_fields=True)
class InteractiveResponseType:
    pass

@strawberry.experimental.pydantic.type(model=NodeDefinition, all_fields=True)
class NodeDefinitionType:
    pass

@strawberry.experimental.pydantic.type(model=Message, all_fields=True)
class MessageType:
    @strawberry.field
    def from_person_id(self) -> str:
        return str(self.from_person_id) if hasattr(self, 'from_person_id') else ""
    
    @strawberry.field
    def message_type(self) -> str:
        return self.message_type if hasattr(self, 'message_type') else ""

@strawberry.experimental.pydantic.type(model=ConversationMetadata, all_fields=True)
class ConversationMetadataType:
    pass

@strawberry.experimental.pydantic.type(model=Conversation, all_fields=True)
class ConversationType:
    pass

# Export all types
__all__ = [
    # Scalar types
    'NodeIDScalar',
    'HandleIDScalar',
    'ArrowIDScalar',
    'PersonIDScalar',
    'ApiKeyIDScalar',
    'DiagramIDScalar',
    'ExecutionIDScalar',
    'HookIDScalar',
    'TaskIDScalar',
    'JSONScalar',
    # Enum types
    'NodeTypeEnum',
    'HandleDirectionEnum',
    'HandleLabelEnum',
    'DataTypeEnum',
    'MemoryViewEnum',
    'DiagramFormatEnum',
    'DBBlockSubTypeEnum',
    'ContentTypeEnum',
    'SupportedLanguageEnum',
    'HttpMethodEnum',
    'HookTypeEnum',
    'HookTriggerModeEnum',
    'ExecutionStatusEnum',
    'NodeExecutionStatusEnum',
    'EventTypeEnum',
    'LLMServiceEnum',
    'APIServiceTypeEnum',
    'NotionOperationEnum',
    'ToolTypeEnum',
    # Domain types
    'Vec2Type',
    'TokenUsageType',
    'NodeStateType',
    'DomainHandleType',
    'DomainNodeType',
    'DomainArrowType',
    'PersonLLMConfigType',
    'MemorySettingsType',
    'DomainPersonType',
    'DomainApiKeyType',
    'DiagramMetadataType',
    'DomainDiagramType',
    'ExecutionOptionsType',
    'ExecutionStateType',
    'InteractivePromptDataType',
    'InteractiveResponseType',
    'NodeDefinitionType',
    'MessageType',
    'ConversationMetadataType',
    'ConversationType',
]