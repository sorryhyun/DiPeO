"""
Strawberry GraphQL types using Pydantic models as single source of truth.
This replaces the manual type definitions with automatic conversions.
"""
import strawberry
from typing import Optional, List, Any

from ..types.scalars import JSONScalar

from apps.server.src.models.domain_graphql import (
    DomainHandle, DomainNode, DomainArrow, DomainPerson,
    DomainApiKey, DiagramMetadata, DiagramForGraphQL,
    ExecutionState as PydanticExecutionState,
    ExecutionEvent as PydanticExecutionEvent,
    TokenUsage as PydanticTokenUsage,
    Vec2 as PydanticVec2
)

# Convert basic types
@strawberry.experimental.pydantic.type(model=PydanticVec2, all_fields=True)
class Vec2:
    """2D position vector."""
    pass

@strawberry.experimental.pydantic.type(model=PydanticTokenUsage, all_fields=True)
class TokenUsage:
    """Token usage statistics."""
    pass

# Convert domain models to Strawberry types
@strawberry.experimental.pydantic.type(model=DomainHandle, all_fields=True)
class Handle:
    """Connection point on a node."""
    pass

@strawberry.experimental.pydantic.type(model=DomainNode)
class Node:
    """Node in a diagram."""
    id: strawberry.auto
    type: strawberry.auto
    position: strawberry.auto
    
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        """Node data as JSON scalar."""
        # Access the original pydantic model data
        return self.__pydantic_model__.data
    
    @strawberry.field
    def display_name(self) -> str:
        """Computed display name for the node."""
        return self.__pydantic_model__.display_name
    
    @strawberry.field
    def handles(self, info) -> List[Handle]:
        """Get handles associated with this node (virtual field for nested view)."""
        # Get handle_index from context if available
        handle_index = getattr(info.context, 'handle_index', None)
        if handle_index is None:
            return []
        
        # Return handles for this node from the index
        return handle_index.get(self.id, [])

@strawberry.experimental.pydantic.type(model=DomainArrow)
class Arrow:
    """Connection between two handles."""
    id: strawberry.auto
    source: strawberry.auto
    target: strawberry.auto
    
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        """Arrow data as JSON scalar."""
        return self.__pydantic_model__.data

@strawberry.experimental.pydantic.type(model=DomainPerson)
class Person:
    """Person (LLM agent) configuration."""
    id: strawberry.auto
    label: strawberry.auto
    service: strawberry.auto
    model: strawberry.auto
    apiKeyId: strawberry.auto
    systemPrompt: strawberry.auto
    forgettingMode: strawberry.auto
    type: strawberry.auto
    
    @strawberry.field
    def masked_api_key(self) -> Optional[str]:
        """Return masked API key for display."""
        return self.__pydantic_model__.masked_api_key

@strawberry.experimental.pydantic.type(model=DomainApiKey)
class ApiKey:
    """API key configuration - excludes actual key."""
    id: strawberry.auto
    label: strawberry.auto
    service: strawberry.auto
    
    @strawberry.field
    def masked_key(self) -> str:
        """Masked version of the key."""
        return self.__pydantic_model__.masked_key

@strawberry.experimental.pydantic.type(model=DiagramMetadata, all_fields=True)
class DiagramMetadata:
    """Metadata for a diagram."""
    pass

@strawberry.experimental.pydantic.type(model=DiagramForGraphQL)
class Diagram:
    """Complete diagram with all components."""
    nodes: strawberry.auto
    handles: strawberry.auto
    arrows: strawberry.auto
    persons: strawberry.auto
    api_keys: strawberry.auto
    metadata: strawberry.auto
    
    @strawberry.field
    def node_count(self) -> int:
        """Total number of nodes."""
        return self.__pydantic_model__.node_count
    
    @strawberry.field
    def arrow_count(self) -> int:
        """Total number of arrows."""
        return self.__pydantic_model__.arrow_count
    
    @strawberry.field
    def person_count(self) -> int:
        """Total number of persons."""
        return self.__pydantic_model__.person_count
    
    @strawberry.field
    async def estimated_cost(self, info) -> Optional[float]:
        """Estimated execution cost based on LLM usage."""
        # TODO: Calculate based on persons and their models
        return None

@strawberry.experimental.pydantic.type(model=PydanticExecutionState)
class ExecutionState:
    """Current state of a diagram execution."""
    id: strawberry.auto
    status: strawberry.auto
    diagram_id: strawberry.auto
    started_at: strawberry.auto
    ended_at: strawberry.auto
    running_nodes: strawberry.auto
    completed_nodes: strawberry.auto
    skipped_nodes: strawberry.auto
    paused_nodes: strawberry.auto
    failed_nodes: strawberry.auto
    token_usage: strawberry.auto
    error: strawberry.auto
    
    @strawberry.field
    def node_outputs(self) -> Optional[JSONScalar]:
        """Node outputs as JSON scalar."""
        return self.__pydantic_model__.node_outputs
    
    @strawberry.field
    def variables(self) -> Optional[JSONScalar]:
        """Variables as JSON scalar."""
        return self.__pydantic_model__.variables
    
    @strawberry.field
    def duration_seconds(self) -> Optional[float]:
        """Execution duration in seconds."""
        return self.__pydantic_model__.duration_seconds
    
    @strawberry.field
    def is_active(self) -> bool:
        """Whether execution is still active."""
        return self.__pydantic_model__.is_active

@strawberry.experimental.pydantic.type(model=PydanticExecutionEvent)
class ExecutionEvent:
    """Event during diagram execution."""
    execution_id: strawberry.auto
    sequence: strawberry.auto
    event_type: strawberry.auto
    node_id: strawberry.auto
    timestamp: strawberry.auto
    
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        """Event data as JSON scalar."""
        return self.__pydantic_model__.data
    
    @strawberry.field
    def formatted_message(self) -> str:
        """Human-readable event message."""
        return self.__pydantic_model__.formatted_message

# Note: Enums are handled by Pydantic models directly, no need to import from .enums