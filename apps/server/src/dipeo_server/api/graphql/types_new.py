"""
GraphQL types for DiPeO server.
This module imports auto-generated types and adds server-specific customizations.
"""

# Import all generated types
from .__generated__.types import (
    # Scalars
    NodeID, ArrowID, HandleID, PersonID, ApiKeyID, DiagramID, ExecutionID, JSONScalar,
    
    # Enums
    NodeTypeEnum, HandleDirectionEnum, HandleLabelEnum, DataTypeEnum,
    MemoryViewEnum, DiagramFormatEnum, DBBlockSubTypeEnum, ContentTypeEnum,
    SupportedLanguageEnum, HttpMethodEnum, HookTypeEnum, HookTriggerModeEnum,
    ExecutionStatusEnum, NodeExecutionStatusEnum, EventTypeEnum,
    LLMServiceEnum, APIServiceTypeEnum, NotionOperationEnum, ToolTypeEnum,
    
    # Types
    Vec2Type, TokenUsageType, NodeStateType, DomainHandleType,
    DiagramMetadataType, DomainNodeType, DomainArrowType,
    PersonLLMConfigType, DomainPersonType, DomainApiKeyType,
    DomainDiagramType, ExecutionStateType, ExecutionOptionsType,
    InteractivePromptDataType, InteractiveResponseType, NodeDefinitionType,
    MessageType, ConversationMetadataType, ConversationType,
    BaseNodeData, StartNodeDataType, ConditionNodeDataType,
    PersonJobNodeDataType, CodeJobNodeDataType, ApiJobNodeDataType,
    EndpointNodeDataType, DBNodeDataType, UserResponseNodeDataType,
    NotionNodeDataType, HookNodeDataType, TemplateJobNodeDataType,
    JsonSchemaValidatorNodeDataType, TypescriptAstNodeData,
    SubDiagramNodeDataType, PersonBatchJobNodeData, ToolConfigType, WebSearchResultType,
    ImageGenerationResultType, ToolOutputType, ChatResultType,
    LLMRequestOptionsType, MemorySettingsType,
    
    # Input Types
    ExecutionUpdate,
    
    # Unions
    NodeData
)

# Re-export enums and domain models for backward compatibility
from dipeo.diagram_generated.enums import (
    NodeType, HandleDirection, HandleLabel, DataType, MemoryView,
    DiagramFormat, DBBlockSubType, ContentType, SupportedLanguage,
    HttpMethod, HookType, HookTriggerMode, ExecutionStatus,
    NodeExecutionStatus, EventType, LLMService, APIServiceType,
    NotionOperation, ToolType
)

from dipeo.diagram_generated.domain_models import (
    Vec2, TokenUsage, NodeState, DomainHandle, DiagramMetadata,
    DomainNode, DomainArrow, PersonLLMConfig, DomainPerson,
    DomainApiKey, DomainDiagram, ExecutionState, ExecutionOptions,
    InteractivePromptData, InteractiveResponse, NodeDefinition,
    Message, ConversationMetadata, Conversation,
    MemorySettings, ToolConfig, WebSearchResult,
    ImageGenerationResult, ToolOutput, ChatResult,
    LLMRequestOptions
)

# Import node data types from individual model files
from dipeo.diagram_generated.models.start_model import StartNodeData
from dipeo.diagram_generated.models.condition_model import ConditionNodeData
from dipeo.diagram_generated.models.person_job_model import PersonJobNodeData
from dipeo.diagram_generated.models.code_job_model import CodeJobNodeData
from dipeo.diagram_generated.models.api_job_model import ApiJobNodeData
from dipeo.diagram_generated.models.endpoint_model import EndpointNodeData
from dipeo.diagram_generated.models.db_model import DbNodeData
from dipeo.diagram_generated.models.user_response_model import UserResponseNodeData
from dipeo.diagram_generated.models.notion_model import NotionNodeData
from dipeo.diagram_generated.models.hook_model import HookNodeData
from dipeo.diagram_generated.models.template_job_model import TemplateJobNodeData
from dipeo.diagram_generated.models.json_schema_validator_model import JsonSchemaValidatorNodeData
from dipeo.diagram_generated.models.typescript_ast_model import TypescriptAstNodeData
from dipeo.diagram_generated.models.sub_diagram_model import SubDiagramNodeData
from dipeo.diagram_generated.models.person_batch_job_model import PersonBatchJobNodeData

# Create a fixed DomainPerson model without the literal type field
from typing import Literal as TypingLiteral

# Import additional server-specific types
import strawberry
from typing import Optional, List
from datetime import datetime


# ============ Server-specific Input Types ============

@strawberry.input
class Vec2Input:
    x: float
    y: float


@strawberry.input
class CreateNodeInput:
    type: NodeType
    position: Vec2Input
    data: JSONScalar


@strawberry.input
class UpdateNodeInput:
    position: Optional[Vec2Input] = None
    data: Optional[JSONScalar] = None


@strawberry.input
class CreateArrowInput:
    source: HandleID
    target: HandleID
    label: Optional[str] = None
    data: Optional[JSONScalar] = None


@strawberry.input
class CreateDiagramInput:
    name: str
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = strawberry.field(default_factory=list)


@strawberry.input
class UpdateDiagramInput:
    name: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None


@strawberry.input
class PersonLLMConfigInput:
    service: LLMService
    model: str
    api_key_id: ApiKeyID
    system_prompt: Optional[str] = None


@strawberry.input
class CreatePersonInput:
    label: str
    llm_config: PersonLLMConfigInput
    type: str = "user"


@strawberry.input
class CreateApiKeyInput:
    label: str
    service: APIServiceType
    key: str


@strawberry.input
class ExecuteDiagramInput:
    diagram_id: Optional[DiagramID] = None
    diagram_data: Optional[JSONScalar] = None
    variables: Optional[JSONScalar] = None
    debug_mode: Optional[bool] = None
    max_iterations: Optional[int] = None
    timeout_seconds: Optional[int] = None


@strawberry.input
class FileOperationInput:
    diagram_id: DiagramID
    format: DiagramFormat


@strawberry.input
class UpdateNodeStateInput:
    execution_id: ExecutionID
    node_id: NodeID
    status: NodeExecutionStatus
    output: Optional[JSONScalar] = None
    error: Optional[str] = None


# ============ Server-specific Result Types ============

@strawberry.type
class DiagramOperationResult:
    success: bool
    message: Optional[str] = None
    diagram: Optional[DomainDiagramType] = None
    error: Optional[str] = None


@strawberry.type
class ExecutionResult:
    success: bool
    execution_id: Optional[ExecutionID] = None
    execution: Optional[ExecutionStateType] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class FileOperationResult:
    success: bool
    message: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class PersonResult:
    success: bool
    person: Optional[DomainPersonType] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class ApiKeyResult:
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    api_key: Optional[DomainApiKeyType] = None


@strawberry.type
class DeleteResult:
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class DiagramResult:
    success: bool
    diagram: Optional[DomainDiagramType] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class NodeResult:
    success: bool
    node: Optional[DomainNodeType] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class FileUploadResult:
    success: bool
    message: Optional[str] = None
    path: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class TestApiKeyResult:
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    model_info: Optional[JSONScalar] = None


@strawberry.type
class DiagramFormatInfo:
    format: str
    name: str
    extension: str
    supports_export: bool
    supports_import: bool
    description: Optional[str] = None


# ============ Additional Input Types ============

@strawberry.input
class UpdatePersonInput:
    label: Optional[str] = None
    llm_config: Optional[PersonLLMConfigInput] = None


@strawberry.input
class DiagramFilterInput:
    name: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@strawberry.input
class ExecutionFilterInput:
    diagram_id: Optional[DiagramID] = None
    status: Optional[ExecutionStatusEnum] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None


@strawberry.input
class ExecutionControlInput:
    execution_id: ExecutionID
    action: str  # "pause", "resume", "cancel"
    reason: Optional[str] = None


@strawberry.input
class InteractiveResponseInput:
    execution_id: ExecutionID
    node_id: NodeID
    response: str
    metadata: Optional[JSONScalar] = None


# ============ Export all types ============

__all__ = [
    # Scalars
    'NodeID', 'ArrowID', 'HandleID', 'PersonID', 'ApiKeyID',
    'DiagramID', 'ExecutionID', 'JSONScalar',
    
    # Enums
    'NodeTypeEnum', 'HandleDirectionEnum', 'HandleLabelEnum', 'DataTypeEnum',
    'MemoryViewEnum', 'DiagramFormatEnum', 'DBBlockSubTypeEnum', 'ContentTypeEnum',
    'SupportedLanguageEnum', 'HttpMethodEnum', 'HookTypeEnum', 'HookTriggerModeEnum',
    'ExecutionStatusEnum', 'NodeExecutionStatusEnum', 'EventTypeEnum',
    'LLMServiceEnum', 'APIServiceTypeEnum', 'NotionOperationEnum', 'ToolTypeEnum',
    
    # Domain model enums (for backward compatibility)
    'NodeType', 'HandleDirection', 'HandleLabel', 'DataType', 'MemoryView',
    'DiagramFormat', 'DBBlockSubType', 'ContentType', 'SupportedLanguage',
    'HttpMethod', 'HookType', 'HookTriggerMode', 'ExecutionStatus',
    'NodeExecutionStatus', 'EventType', 'LLMService', 'APIServiceType',
    'NotionOperation', 'ToolType',
    
    # Types
    'Vec2Type', 'TokenUsageType', 'NodeStateType', 'DomainHandleType',
    'DiagramMetadataType', 'DomainNodeType', 'DomainArrowType',
    'PersonLLMConfigType', 'DomainPersonType', 'DomainApiKeyType',
    'DomainDiagramType', 'ExecutionStateType', 'ExecutionOptionsType',
    'InteractivePromptDataType', 'InteractiveResponseType', 'NodeDefinitionType',
    'MessageType', 'ConversationMetadataType', 'ConversationType',
    'BaseNodeData', 'StartNodeDataType', 'ConditionNodeDataType',
    'PersonJobNodeDataType', 'CodeJobNodeDataType', 'ApiJobNodeDataType',
    'EndpointNodeDataType', 'DBNodeDataType', 'UserResponseNodeDataType',
    'NotionNodeDataType', 'HookNodeDataType', 'TemplateJobNodeDataType',
    'JsonSchemaValidatorNodeDataType', 'TypescriptAstNodeData',
    'SubDiagramNodeDataType', 'PersonBatchJobNodeData', 'ToolConfigType', 'WebSearchResultType',
    'ImageGenerationResultType', 'ToolOutputType', 'ChatResultType',
    'LLMRequestOptionsType', 'MemorySettingsType',
    
    # Input Types
    'Vec2Input', 'CreateNodeInput', 'UpdateNodeInput', 'CreateArrowInput',
    'CreateDiagramInput', 'UpdateDiagramInput', 'CreatePersonInput',
    'PersonLLMConfigInput', 'CreateApiKeyInput', 'ExecuteDiagramInput',
    'FileOperationInput', 'UpdateNodeStateInput', 'ExecutionUpdate',
    
    # Result Types
    'DiagramOperationResult', 'ExecutionResult', 'FileOperationResult',
    'PersonResult', 'ApiKeyResult', 'DeleteResult', 'DiagramResult',
    'NodeResult', 'FileUploadResult', 'TestApiKeyResult', 'DiagramFormatInfo',
    
    # Additional Input Types
    'UpdatePersonInput', 'DiagramFilterInput', 'ExecutionFilterInput',
    'ExecutionControlInput', 'InteractiveResponseInput',
    
    # Unions
    'NodeData',
    
    # Domain models (for backward compatibility)
    'Vec2', 'TokenUsage', 'NodeState', 'DomainHandle', 'DiagramMetadata',
    'DomainNode', 'DomainArrow', 'PersonLLMConfig', 'DomainPerson',
    'DomainApiKey', 'DomainDiagram', 'ExecutionState', 'ExecutionOptions',
    'InteractivePromptData', 'InteractiveResponse', 'NodeDefinition',
    'Message', 'ConversationMetadata', 'Conversation',
    'StartNodeData', 'ConditionNodeData', 'PersonJobNodeData',
    'CodeJobNodeData', 'ApiJobNodeData', 'EndpointNodeData',
    'DbNodeData', 'UserResponseNodeData', 'NotionNodeData',
    'HookNodeData', 'TemplateJobNodeData', 'JsonSchemaValidatorNodeData',
    'TypescriptAstNodeData', 'SubDiagramNodeData', 'PersonBatchJobNodeData',
    'MemorySettings', 'ToolConfig', 'WebSearchResult',
    'ImageGenerationResult', 'ToolOutput', 'ChatResult',
    'LLMRequestOptions'
]