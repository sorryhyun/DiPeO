"""
Strawberry GraphQL domain types for DiPeO.
Auto-generated from TypeScript interfaces.

Generated at: 2025-09-17T16:05:06.250858
"""

import strawberry
from typing import Optional, Dict, Any, List
from strawberry.scalars import JSON as JSONScalar

# Import the Pydantic domain models
from dipeo.diagram_generated.domain_models import (
    CliSession,
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
    InteractivePromptData,
    ExecutionUpdate,
    NodeDefinition,
    File,
    ExecutionOptions,
    ToolConfig,
    ToolOutput,
    NodeUpdate,
    InteractivePrompt,
    ExecutionLogEntry,
    KeepalivePayload,
)

# Import the Status enum for GraphQL type resolution
from dipeo.diagram_generated.enums import Status

# Import scalar types
from .scalars import (
    CliSessionIDScalar,
    NodeIDScalar,
    ArrowIDScalar,
    HandleIDScalar,
    PersonIDScalar,
    ApiKeyIDScalar,
    DiagramIDScalar,
    HookIDScalar,
    TaskIDScalar,
    ExecutionIDScalar,
    FileIDScalar,
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

# DomainNode has JsonDict field that needs manual conversion
@strawberry.type
class DomainNodeType:
    id: NodeIDScalar
    type: str  # NodeType enum
    position: Vec2Type
    data: JSONScalar  # JsonDict converted to JSON

    @staticmethod
    def from_pydantic(obj: DomainNode) -> "DomainNodeType":
        """Convert from Pydantic model"""
        # Vec2Type is a pydantic type, use its from_pydantic method
        position = Vec2Type.from_pydantic(obj.position) if hasattr(Vec2Type, 'from_pydantic') else Vec2Type(x=obj.position.x, y=obj.position.y)
        return DomainNodeType(
            id=obj.id,
            type=str(obj.type.value) if hasattr(obj.type, 'value') else str(obj.type),
            position=position,
            data=obj.data  # Will be serialized as JSON
        )

# DomainArrow has Literal type that needs manual conversion
@strawberry.type
class DomainArrowType:
    id: ArrowIDScalar
    source: HandleIDScalar
    target: HandleIDScalar
    content_type: Optional[str] = None  # ContentType enum
    label: Optional[str] = None
    packing: Optional[str] = None  # Literal["pack", "spread"]
    execution_priority: Optional[float] = None

    @staticmethod
    def from_pydantic(obj: DomainArrow) -> "DomainArrowType":
        """Convert from Pydantic model"""
        return DomainArrowType(
            id=obj.id,
            source=obj.source,
            target=obj.target,
            content_type=str(obj.content_type.value) if obj.content_type and hasattr(obj.content_type, 'value') else str(obj.content_type) if obj.content_type else None,
            label=obj.label,
            packing=obj.packing,
            execution_priority=obj.execution_priority
        )

@strawberry.experimental.pydantic.type(PersonLLMConfig, all_fields=True)
class PersonLLMConfigType:
    pass

# DomainPerson has Literal type that needs manual conversion
@strawberry.type
class DomainPersonType:
    id: PersonIDScalar
    label: str
    llm_config: PersonLLMConfigType
    type: str  # Literal["person"]

    @staticmethod
    def from_pydantic(obj: DomainPerson) -> "DomainPersonType":
        """Convert from Pydantic model"""
        return DomainPersonType(
            id=obj.id,
            label=obj.label,
            llm_config=PersonLLMConfigType.from_pydantic(obj.llm_config),
            type=obj.type
        )

@strawberry.experimental.pydantic.type(DomainApiKey, all_fields=True)
class DomainApiKeyType:
    pass

@strawberry.experimental.pydantic.type(DiagramMetadata, all_fields=True)
class DiagramMetadataType:
    pass

# DomainDiagram has list of DomainNode which needs manual conversion
@strawberry.type
class DomainDiagramType:
    nodes: list[DomainNodeType]
    handles: list[DomainHandleType]
    arrows: list[DomainArrowType]
    persons: list[DomainPersonType]
    metadata: Optional["DiagramMetadataType"] = None

    @staticmethod
    def from_pydantic(obj: DomainDiagram) -> "DomainDiagramType":
        """Convert from Pydantic model"""
        return DomainDiagramType(
            nodes=[DomainNodeType.from_pydantic(n) for n in obj.nodes],
            handles=[DomainHandleType.from_pydantic(h) for h in obj.handles],
            arrows=[DomainArrowType.from_pydantic(a) for a in obj.arrows],
            persons=[DomainPersonType.from_pydantic(p) for p in obj.persons],
            metadata=DiagramMetadataType.from_pydantic(obj.metadata) if obj.metadata else None
        )

@strawberry.experimental.pydantic.type(LLMUsage, all_fields=True)
class LLMUsageType:
    pass

@strawberry.experimental.pydantic.type(NodeState, all_fields=True)
class NodeStateType:
    pass

@strawberry.experimental.pydantic.type(NodeMetrics, all_fields=True)
class NodeMetricsType:
    pass

@strawberry.experimental.pydantic.type(Bottleneck, all_fields=True)
class BottleneckType:
    pass

# ExecutionMetrics has dict field that needs manual conversion
@strawberry.type
class ExecutionMetricsType:
    execution_id: ExecutionIDScalar
    start_time: float
    end_time: Optional[float] = None
    total_duration_ms: Optional[float] = None
    node_metrics: JSONScalar  # dict[str, NodeMetrics] as JSON
    critical_path: Optional[list[str]] = None
    parallelizable_groups: Optional[list[list[str]]] = None
    bottlenecks: Optional[list[BottleneckType]] = None
    total_llm_tokens: Optional[int] = None
    total_llm_calls: Optional[int] = None

    @staticmethod
    def from_pydantic(obj: ExecutionMetrics) -> "ExecutionMetricsType":
        """Convert from Pydantic model"""
        bottlenecks = None
        if obj.bottlenecks:
            bottlenecks = [BottleneckType.from_pydantic(b) if hasattr(BottleneckType, 'from_pydantic') else b for b in obj.bottlenecks]

        return ExecutionMetricsType(
            execution_id=obj.execution_id,
            start_time=obj.start_time,
            end_time=obj.end_time,
            total_duration_ms=obj.total_duration_ms,
            node_metrics=obj.node_metrics,  # Will be serialized as JSON
            critical_path=obj.critical_path,
            parallelizable_groups=obj.parallelizable_groups,
            bottlenecks=bottlenecks,
            total_llm_tokens=obj.total_llm_tokens,
            total_llm_calls=obj.total_llm_calls
        )

@strawberry.experimental.pydantic.type(EnvelopeMeta, all_fields=True)
class EnvelopeMetaType:
    pass

@strawberry.experimental.pydantic.type(SerializedEnvelope, all_fields=True)
class SerializedEnvelopeType:
    pass

# ExecutionState has dict fields that need manual conversion
@strawberry.type
class ExecutionStateType:
    id: ExecutionIDScalar
    status: str  # Status enum
    diagram_id: Optional[DiagramIDScalar] = None
    started_at: str
    ended_at: Optional[str] = None
    node_states: JSONScalar  # dict[str, NodeState] as JSON
    node_outputs: JSONScalar  # dict[str, SerializedNodeOutput] as JSON
    llm_usage: LLMUsageType
    error: Optional[str] = None
    variables: Optional[JSONScalar] = None  # JsonDict
    metadata: Optional[JSONScalar] = None  # JsonDict
    duration_seconds: Optional[float] = None
    is_active: Optional[bool] = None
    exec_counts: JSONScalar  # dict[str, float] as JSON
    executed_nodes: list[str]
    metrics: Optional[ExecutionMetricsType] = None

    @staticmethod
    def from_pydantic(obj: ExecutionState) -> "ExecutionStateType":
        """Convert from Pydantic model"""
        # LLMUsageType and ExecutionMetricsType use pydantic decorator, so pass the object directly
        llm_usage = LLMUsageType.from_pydantic(obj.llm_usage) if hasattr(LLMUsageType, 'from_pydantic') else obj.llm_usage
        metrics = None
        if obj.metrics:
            metrics = ExecutionMetricsType.from_pydantic(obj.metrics) if hasattr(ExecutionMetricsType, 'from_pydantic') else obj.metrics

        # Convert node_states dict with NodeState objects to JSON-serializable dict
        node_states_dict = {}
        if obj.node_states:
            for key, node_state in obj.node_states.items():
                if hasattr(node_state, 'model_dump'):
                    node_states_dict[key] = node_state.model_dump()
                else:
                    node_states_dict[key] = node_state

        # Convert node_outputs dict to JSON-serializable dict
        node_outputs_dict = {}
        if obj.node_outputs:
            for key, output in obj.node_outputs.items():
                if hasattr(output, 'model_dump'):
                    node_outputs_dict[key] = output.model_dump()
                else:
                    node_outputs_dict[key] = output

        return ExecutionStateType(
            id=obj.id,
            status=str(obj.status.value) if hasattr(obj.status, 'value') else str(obj.status),
            diagram_id=obj.diagram_id,
            started_at=obj.started_at,
            ended_at=obj.ended_at,
            node_states=node_states_dict,  # Now properly serialized
            node_outputs=node_outputs_dict,  # Now properly serialized
            llm_usage=llm_usage,
            error=obj.error,
            variables=obj.variables,
            metadata=obj.metadata,
            duration_seconds=obj.duration_seconds,
            is_active=getattr(obj, 'is_active', None),
            exec_counts=obj.exec_counts,  # Will be serialized as JSON
            executed_nodes=obj.executed_nodes,
            metrics=metrics
        )

@strawberry.experimental.pydantic.type(InteractivePromptData, all_fields=True)
class InteractivePromptDataType:
    pass

@strawberry.experimental.pydantic.type(ExecutionUpdate, all_fields=True)
class ExecutionUpdateType:
    pass

@strawberry.experimental.pydantic.type(NodeDefinition, all_fields=True)
class NodeDefinitionType:
    pass

@strawberry.experimental.pydantic.type(ExecutionOptions)
class ExecutionOptionsType:
    mode: strawberry.auto
    timeout: strawberry.auto
    @strawberry.field
    def variables(self) -> JSONScalar:
        """Execution variables"""
        return self.variables if hasattr(self, 'variables') else {}

@strawberry.experimental.pydantic.type(File, all_fields=True)
class FileType:
    pass

@strawberry.experimental.pydantic.type(ToolConfig, all_fields=True)
class ToolConfigType:
    pass

# ToolOutput has complex union types that strawberry can't handle automatically
# So we define it manually
@strawberry.type
class ToolOutputType:
    type: str  # ToolType enum converted to string
    result: JSONScalar  # Union type converted to JSON
    raw_response: Optional[JSONScalar] = None

    @staticmethod
    def from_pydantic(obj: ToolOutput) -> "ToolOutputType":
        """Convert from Pydantic model"""
        return ToolOutputType(
            type=str(obj.type.value) if hasattr(obj.type, 'value') else str(obj.type),
            result=obj.result,  # Will be serialized as JSON
            raw_response=obj.raw_response
        )

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
    'InteractivePromptDataType',
    'ExecutionUpdateType',
    'NodeDefinitionType',
    'FileType',
    'ToolConfigType',
    'ToolOutputType',
    'NodeUpdateType',
    'InteractivePromptType',
    'ExecutionLogEntryType',
    'KeepalivePayloadType',
    'ExecutionUpdate',  # For subscriptions
    'SerializedNodeOutputType',  # Alias
    'ToolConfigType',  # Re-exported from generated code
]
