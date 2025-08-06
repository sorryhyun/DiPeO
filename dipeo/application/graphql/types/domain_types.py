"""
Strawberry GraphQL types for DiPeO domain models.

This module creates Strawberry types from Pydantic domain models
using the @strawberry.experimental.pydantic.type decorator.
"""

import strawberry
from typing import Optional, List, Dict, Any
from strawberry.scalars import JSON as JSONScalar

# Import the Pydantic domain models
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
)

# Import scalar types - this ensures they're registered
from .scalars import (
    NodeIDScalar,
    HandleIDScalar,
    ArrowIDScalar,
    PersonIDScalar,
    ApiKeyIDScalar,
    DiagramIDScalar,
    ExecutionIDScalar,
    HookIDScalar,
    TaskIDScalar,
)

# Create Strawberry types from Pydantic models using experimental decorator
# Order matters - define types that are referenced by others first

@strawberry.experimental.pydantic.type(Vec2, all_fields=True)
class Vec2Type:
    pass

@strawberry.experimental.pydantic.type(TokenUsage, all_fields=True)
class TokenUsageType:
    pass

@strawberry.experimental.pydantic.type(MemorySettings, all_fields=True)
class MemorySettingsType:
    pass

@strawberry.experimental.pydantic.type(PersonLLMConfig, all_fields=True)
class PersonLLMConfigType:
    pass

# NodeState has a Dict field 'output' that needs special handling
@strawberry.experimental.pydantic.type(NodeState)
class NodeStateType:
    status: strawberry.auto
    started_at: strawberry.auto
    ended_at: strawberry.auto
    error: strawberry.auto
    token_usage: strawberry.auto
    
    @strawberry.field
    def output(self) -> Optional[JSONScalar]:
        return self.output if hasattr(self, 'output') else None

@strawberry.experimental.pydantic.type(DomainHandle, all_fields=True)
class DomainHandleType:
    pass

# DomainNode has a Dict field 'data' that needs special handling
@strawberry.experimental.pydantic.type(DomainNode)
class DomainNodeType:
    id: strawberry.auto
    type: strawberry.auto
    position: strawberry.auto
    
    @strawberry.field
    def data(self) -> JSONScalar:
        return self.data if hasattr(self, 'data') else {}

# DomainArrow has an optional Dict field 'data' that needs special handling
@strawberry.experimental.pydantic.type(DomainArrow)
class DomainArrowType:
    id: strawberry.auto
    source: strawberry.auto
    target: strawberry.auto
    content_type: strawberry.auto
    label: strawberry.auto
    
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        return self.data if hasattr(self, 'data') else None

@strawberry.experimental.pydantic.type(DomainPerson)
class DomainPersonType:
    id: strawberry.auto
    label: strawberry.auto
    llm_config: strawberry.auto
    
    @strawberry.field
    def type(self) -> str:
        return "person"

@strawberry.experimental.pydantic.type(DomainApiKey, all_fields=True)
class DomainApiKeyType:
    pass

@strawberry.experimental.pydantic.type(DiagramMetadata, all_fields=True)
class DiagramMetadataType:
    pass

# ExecutionOptions has a Dict field 'variables' that needs special handling
@strawberry.experimental.pydantic.type(ExecutionOptions)
class ExecutionOptionsType:
    mode: strawberry.auto
    timeout: strawberry.auto
    
    @strawberry.field
    def variables(self) -> JSONScalar:
        return self.variables if hasattr(self, 'variables') else {}

# ExecutionState has multiple Dict fields that need special handling
@strawberry.experimental.pydantic.type(ExecutionState)
class ExecutionStateType:
    id: strawberry.auto
    status: strawberry.auto
    diagram_id: strawberry.auto
    started_at: strawberry.auto
    ended_at: strawberry.auto
    token_usage: strawberry.auto
    error: strawberry.auto
    duration_seconds: strawberry.auto
    is_active: strawberry.auto
    executed_nodes: strawberry.auto
    
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
    def variables(self) -> Optional[JSONScalar]:
        return self.variables if hasattr(self, 'variables') else None
    
    @strawberry.field
    def exec_counts(self) -> JSONScalar:
        return self.exec_counts if hasattr(self, 'exec_counts') else {}
    
    @strawberry.field
    def metrics(self) -> Optional[JSONScalar]:
        return self.metrics if hasattr(self, 'metrics') else None

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

# Export all types
__all__ = [
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
]