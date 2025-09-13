"""
Strawberry GraphQL domain types for DiPeO.
Auto-generated from TypeScript interfaces.

Generated at: 2025-09-13T16:47:42.128948
"""

import strawberry
from typing import Optional, Dict, Any, List
from strawberry.scalars import JSON as JSONScalar

# Import the Pydantic domain models
from dipeo.diagram_generated.domain_models import (
    CliSession,
    CliSessionResult,
    Message,
    ConversationMetadata,
    Conversation,
    Vec2,
    DomainHandle,
    DomainNode,
    DomainArrow,
    PersonLLMConfig,
    DomainPerson,
    DomainApiKey,
    DiagramMetadata,
    DomainDiagram,
    LLMUsage,
    NodeState,
    NodeMetrics,
    Bottleneck,
    ExecutionMetrics,
    EnvelopeMeta,
    SerializedEnvelope,
    ExecutionState,
    ExecutionOptions,
    InteractivePromptData,
    InteractiveResponse,
    ExecutionUpdate,
    NodeDefinition,
    File,
    FileOperationResult,
    ToolConfig,
    WebSearchResult,
    ImageGenerationResult,
    ToolOutput,
    ChatResult,
    LLMRequestOptions,
    NodeUpdate,
    InteractivePrompt,
    ExecutionLogEntry,
    KeepalivePayload,
)

# Import the Status enum for GraphQL type resolution
from dipeo.diagram_generated.enums import Status

# Import scalar types
from .scalars import (
    ApiKeyIDScalar,
    ArrowIDScalar,
    DiagramIDScalar,
    ExecutionIDScalar,
    HandleIDScalar,
    HookIDScalar,
    NodeIDScalar,
    PersonIDScalar,
    CliSessionIDScalar,
    FileIDScalar,
    TaskIDScalar,
)

# Note: HookIDScalar and TaskIDScalar are not branded types yet
# TODO: Add these as branded types in TypeScript models
from strawberry.scalars import ID
HookIDScalar = ID  # Temporary fallback
TaskIDScalar = ID  # Temporary fallback

# Import generated types that already exist
from dipeo.diagram_generated.graphql.strawberry_domain import (
    ToolConfigType,
)

# Create Strawberry types from Pydantic models
# Order matters - define types that are referenced by others first
@strawberry.experimental.pydantic.type(CliSession, all_fields=True)
class CliSessionType:
    pass
@strawberry.experimental.pydantic.type(CliSessionResult, all_fields=True)
class CliSessionResultType:
    pass
@strawberry.experimental.pydantic.type(Message, all_fields=True)
class MessageType:
    pass
@strawberry.experimental.pydantic.type(ConversationMetadata, all_fields=True)
class ConversationMetadataType:
    pass
@strawberry.experimental.pydantic.type(Conversation, all_fields=True)
class ConversationType:
    pass
@strawberry.experimental.pydantic.type(Vec2, all_fields=True)
class Vec2Type:
    pass
@strawberry.experimental.pydantic.type(DomainHandle, all_fields=True)
class DomainHandleType:
    pass
@strawberry.experimental.pydantic.type(DomainNode)
class DomainNodeType:
    id: strawberry.auto
    position: strawberry.auto
    @strawberry.field
    def type(self) -> str:
        """Return the enum value (lowercase)"""
        return self.type.value if hasattr(self, 'type') else ''
    @strawberry.field
    def data(self) -> JSONScalar:
        """Node configuration data"""
        return self.data if hasattr(self, 'data') else {}
@strawberry.experimental.pydantic.type(DomainArrow, all_fields=True)
class DomainArrowType:
    pass
@strawberry.experimental.pydantic.type(PersonLLMConfig, all_fields=True)
class PersonLLMConfigType:
    pass
@strawberry.experimental.pydantic.type(DomainPerson, all_fields=True)
class DomainPersonType:
    pass
@strawberry.experimental.pydantic.type(DomainApiKey, all_fields=True)
class DomainApiKeyType:
    pass
@strawberry.experimental.pydantic.type(DiagramMetadata, all_fields=True)
class DiagramMetadataType:
    pass
@strawberry.experimental.pydantic.type(DomainDiagram, all_fields=True)
class DomainDiagramType:
    pass
@strawberry.experimental.pydantic.type(LLMUsage, all_fields=True)
class LLMUsageType:
    pass
@strawberry.experimental.pydantic.type(NodeState)
class NodeStateType:
    status: Status  # Explicitly specify the enum type
    started_at: strawberry.auto
    ended_at: strawberry.auto
    @strawberry.field
    def output(self) -> Optional[JSONScalar]:
        """Node output data"""
        return self.output if hasattr(self, 'output') else None
@strawberry.experimental.pydantic.type(NodeMetrics, all_fields=True)
class NodeMetricsType:
    pass
@strawberry.experimental.pydantic.type(Bottleneck, all_fields=True)
class BottleneckType:
    pass
@strawberry.experimental.pydantic.type(ExecutionMetrics, all_fields=True)
class ExecutionMetricsType:
    pass
@strawberry.experimental.pydantic.type(EnvelopeMeta, all_fields=True)
class EnvelopeMetaType:
    pass
@strawberry.experimental.pydantic.type(SerializedEnvelope, all_fields=True)
class SerializedEnvelopeType:
    pass
@strawberry.experimental.pydantic.type(ExecutionState, all_fields=True)
class ExecutionStateType:
    pass
@strawberry.experimental.pydantic.type(ExecutionOptions, all_fields=True)
class ExecutionOptionsType:
    pass
@strawberry.experimental.pydantic.type(InteractivePromptData, all_fields=True)
class InteractivePromptDataType:
    pass
@strawberry.experimental.pydantic.type(InteractiveResponse, all_fields=True)
class InteractiveResponseType:
    pass
@strawberry.experimental.pydantic.type(ExecutionUpdate, all_fields=True)
class ExecutionUpdateType:
    pass
@strawberry.experimental.pydantic.type(NodeDefinition, all_fields=True)
class NodeDefinitionType:
    pass
@strawberry.experimental.pydantic.type(File, all_fields=True)
class FileType:
    pass
@strawberry.experimental.pydantic.type(FileOperationResult, all_fields=True)
class FileOperationResultType:
    pass
@strawberry.experimental.pydantic.type(ToolConfig, all_fields=True)
class ToolConfigType:
    pass
@strawberry.experimental.pydantic.type(WebSearchResult, all_fields=True)
class WebSearchResultType:
    pass
@strawberry.experimental.pydantic.type(ImageGenerationResult, all_fields=True)
class ImageGenerationResultType:
    pass
@strawberry.experimental.pydantic.type(ToolOutput, all_fields=True)
class ToolOutputType:
    pass
@strawberry.experimental.pydantic.type(ChatResult, all_fields=True)
class ChatResultType:
    pass
@strawberry.experimental.pydantic.type(LLMRequestOptions, all_fields=True)
class LLMRequestOptionsType:
    pass
@strawberry.experimental.pydantic.type(NodeUpdate, all_fields=True)
class NodeUpdateType:
    pass
@strawberry.experimental.pydantic.type(InteractivePrompt, all_fields=True)
class InteractivePromptType:
    pass
@strawberry.experimental.pydantic.type(ExecutionLogEntry, all_fields=True)
class ExecutionLogEntryType:
    pass
@strawberry.experimental.pydantic.type(KeepalivePayload, all_fields=True)
class KeepalivePayloadType:
    pass

# Subscription-specific types (not from Pydantic models)
@strawberry.type
class ExecutionUpdate:
    """Real-time execution update."""

    execution_id: str
    event_type: str
    data: JSONScalar
    timestamp: str

# Alias for backward compatibility
SerializedNodeOutputType = SerializedEnvelopeType

# Export all types
__all__ = [
    'CliSessionType',
    'CliSessionResultType',
    'MessageType',
    'ConversationMetadataType',
    'ConversationType',
    'Vec2Type',
    'DomainHandleType',
    'DomainNodeType',
    'DomainArrowType',
    'PersonLLMConfigType',
    'DomainPersonType',
    'DomainApiKeyType',
    'DiagramMetadataType',
    'DomainDiagramType',
    'LLMUsageType',
    'NodeStateType',
    'NodeMetricsType',
    'BottleneckType',
    'ExecutionMetricsType',
    'EnvelopeMetaType',
    'SerializedEnvelopeType',
    'ExecutionStateType',
    'ExecutionOptionsType',
    'InteractivePromptDataType',
    'InteractiveResponseType',
    'ExecutionUpdateType',
    'NodeDefinitionType',
    'FileType',
    'FileOperationResultType',
    'ToolConfigType',
    'WebSearchResultType',
    'ImageGenerationResultType',
    'ToolOutputType',
    'ChatResultType',
    'LLMRequestOptionsType',
    'NodeUpdateType',
    'InteractivePromptType',
    'ExecutionLogEntryType',
    'KeepalivePayloadType',
    'ExecutionUpdate',  # For subscriptions
    'SerializedNodeOutputType',  # Alias
    'ToolConfigType',  # Re-exported from generated code
]