"""
Strawberry GraphQL domain types for DiPeO.
Auto-generated from TypeScript interfaces.

Generated at: 2025-09-11T15:46:12.776960
"""

import strawberry
from typing import Optional, Dict, Any, List
from strawberry.scalars import JSON as JSONScalar

# Import the Pydantic domain models
from dipeo.diagram_generated.domain_models import (
    Vec2,
    PersonLLMConfig,
    DomainHandle,
    DomainNode,
    DomainArrow,
    DomainPerson,
    DomainApiKey,
    DiagramMetadata,
    DomainDiagram,
    LLMUsage,
    NodeState,
    EnvelopeMeta,
    SerializedEnvelope,
    ExecutionOptions,
    ExecutionState,
)

# Import the Status enum for GraphQL type resolution
from dipeo.diagram_generated.enums import Status

# Import scalar types
from dipeo.diagram_generated.graphql.scalars import (
    ApiKeyIDScalar,
    ArrowIDScalar,
    DiagramIDScalar,
    ExecutionIDScalar,
    HandleIDScalar,
    NodeIDScalar,
    PersonIDScalar,
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
@strawberry.experimental.pydantic.type(Vec2, all_fields=True)
class Vec2Type:
    pass
@strawberry.experimental.pydantic.type(PersonLLMConfig, all_fields=True)
class PersonLLMConfigType:
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
        """Return the enum value (lowercase) instead of the enum name."""
        return self.type.value if hasattr(self, 'type') else ''
    @strawberry.field
    def data(self) -> JSONScalar:
        """Node configuration data"""
        return self.data if hasattr(self, 'data') else {}
@strawberry.experimental.pydantic.type(DomainArrow)
class DomainArrowType:
    id: strawberry.auto
    source: strawberry.auto
    target: strawberry.auto
    content_type: strawberry.auto
    label: strawberry.auto
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        """Optional arrow data"""
        return self.data if hasattr(self, 'data') else None
@strawberry.experimental.pydantic.type(DomainPerson)
class DomainPersonType:
    id: strawberry.auto
    label: strawberry.auto
    llm_config: strawberry.auto
    @strawberry.field
    def type(self) -> str:
        """Always returns person"""
        return "person"
@strawberry.experimental.pydantic.type(DomainApiKey, all_fields=True)
class DomainApiKeyType:
    pass
@strawberry.experimental.pydantic.type(DiagramMetadata, all_fields=True)
class DiagramMetadataType:
    pass
@strawberry.experimental.pydantic.type(DomainDiagram, all_fields=True)
class DomainDiagramType:
    @strawberry.field
    def nodeCount(self) -> int:
        """Returns the total number of nodes in the diagram"""
        return len(self.nodes) if hasattr(self, 'nodes') else 0
    @strawberry.field
    def arrowCount(self) -> int:
        """Returns the total number of arrows in the diagram"""
        return len(self.arrows) if hasattr(self, 'arrows') else 0
@strawberry.experimental.pydantic.type(LLMUsage, all_fields=True)
class LLMUsageType:
    pass
@strawberry.experimental.pydantic.type(NodeState)
class NodeStateType:
    status: Status  # Explicitly specify the enum type
    started_at: strawberry.auto
    ended_at: strawberry.auto
    error: strawberry.auto
    llm_usage: strawberry.auto
    @strawberry.field
    def output(self) -> Optional[JSONScalar]:
        """Node output data"""
        return self.output if hasattr(self, 'output') else None
@strawberry.experimental.pydantic.type(EnvelopeMeta)
class EnvelopeMetaType:
    node_id: Optional[Optional[str]] = None
    llm_usage: Optional[Optional[LLMUsageType]] = None
    execution_time: Optional[Optional[float]] = None
    retry_count: Optional[Optional[int]] = None
    error: Optional[Optional[str]] = None
    error_type: Optional[Optional[str]] = None
    timestamp: Optional[Optional[JSONScalar]] = None
@strawberry.experimental.pydantic.type(SerializedEnvelope)
class SerializedEnvelopeType:
    envelope_format: strawberry.auto
    id: strawberry.auto
    trace_id: strawberry.auto
    produced_by: strawberry.auto
    content_type: strawberry.auto
    schema_id: strawberry.auto
    serialization_format: strawberry.auto
    body: Optional[Optional[JSONScalar]] = None
    meta: strawberry.auto
@strawberry.experimental.pydantic.type(ExecutionOptions)
class ExecutionOptionsType:
    mode: strawberry.auto
    timeout: strawberry.auto
    @strawberry.field
    def variables(self) -> JSONScalar:
        """Execution variables"""
        return self.variables if hasattr(self, 'variables') else {}
@strawberry.experimental.pydantic.type(ExecutionState)
class ExecutionStateType:
    id: strawberry.auto
    status: Status  # Explicitly specify the enum type
    diagram_id: strawberry.auto
    started_at: strawberry.auto
    ended_at: strawberry.auto
    llm_usage: strawberry.auto
    error: strawberry.auto
    duration_seconds: strawberry.auto
    is_active: strawberry.auto
    executed_nodes: strawberry.auto
    @strawberry.field
    def node_states(self) -> JSONScalar:
        """Node execution states"""
        if hasattr(self, 'node_states') and self.node_states:
            # Convert NodeState objects to dicts
            return {k: v.model_dump() if hasattr(v, 'model_dump') else v
                    for k, v in self.node_states.items()}
        return {}
    @strawberry.field
    def node_outputs(self) -> JSONScalar:
        """Node execution outputs"""
        if hasattr(self, 'node_outputs') and self.node_outputs:
            # Convert SerializedNodeOutput objects to dicts for GraphQL
            result = {}
            for key, output in self.node_outputs.items():
                if hasattr(output, 'model_dump'):
                    result[key] = output.model_dump()
                else:
                    result[key] = output
            return result
        return {}
    @strawberry.field
    def variables(self) -> Optional[JSONScalar]:
        """Execution variables"""
        return self.variables if hasattr(self, 'variables') else None
    @strawberry.field
    def exec_counts(self) -> JSONScalar:
        """Node execution counts"""
        return self.exec_counts if hasattr(self, 'exec_counts') else {}
    @strawberry.field
    def metrics(self) -> Optional[JSONScalar]:
        """Execution metrics"""
        return self.metrics if hasattr(self, 'metrics') else None

# Alias for backward compatibility
SerializedNodeOutputType = SerializedEnvelopeType

# Export all types
__all__ = [
    'Vec2Type',
    'PersonLLMConfigType',
    'DomainHandleType',
    'DomainNodeType',
    'DomainArrowType',
    'DomainPersonType',
    'DomainApiKeyType',
    'DiagramMetadataType',
    'DomainDiagramType',
    'LLMUsageType',
    'NodeStateType',
    'EnvelopeMetaType',
    'SerializedEnvelopeType',
    'ExecutionOptionsType',
    'ExecutionStateType',
    'SerializedNodeOutputType',  # Alias
    'ToolConfigType',  # Re-exported from generated code
]