"""
Strawberry GraphQL types using Pydantic models as single source of truth.
This replaces the manual type definitions with automatic conversions.
"""
import strawberry
from typing import Optional, List

from ..types.scalars import JSONScalar, DiagramID, ExecutionID

from src.domains.diagram.models.domain import (
    DomainHandle, DomainNode, DomainArrow, DomainPerson,
    DomainApiKey, DiagramMetadata, DiagramForGraphQL,
    ExecutionState as PydanticExecutionState,
    ExecutionEvent as PydanticExecutionEvent
)
from src.shared.domain import (
    TokenUsage as PydanticTokenUsage,
    Vec2 as PydanticVec2,
    DiagramFormat
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
        # Access the data field directly
        return self.data if hasattr(self, 'data') else None
    
    @strawberry.field
    def display_name(self) -> str:
        """Computed display name for the node."""
        # Get from data field if available
        if hasattr(self, 'data') and self.data:
            return self.data.get('label', f'{self.type} node')
        return f'{self.type} node'
    
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
        return self.data if hasattr(self, 'data') else None

@strawberry.experimental.pydantic.type(model=DomainPerson)
class Person:
    """Person (LLM agent) configuration."""
    id: strawberry.auto
    label: strawberry.auto
    service: strawberry.auto
    model: strawberry.auto
    api_key_id: strawberry.auto
    systemPrompt: strawberry.auto
    forgettingMode: strawberry.auto
    type: strawberry.auto
    
    @strawberry.field
    def masked_api_key(self) -> Optional[str]:
        """Return masked API key for display."""
        if not self.api_key_id:
            return None
        return f"****{str(self.api_key_id)[-4:]}"

@strawberry.experimental.pydantic.type(model=DomainApiKey)
class ApiKey:
    """API key configuration - excludes actual key."""
    id: strawberry.auto
    label: strawberry.auto
    service: strawberry.auto
    
    @strawberry.field
    def masked_key(self) -> str:
        """Masked version of the key."""
        return f"{self.service.value}-****"

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
        return len(self.nodes)
    
    @strawberry.field
    def arrow_count(self) -> int:
        """Total number of arrows."""
        return len(self.arrows)
    
    @strawberry.field
    def person_count(self) -> int:
        """Total number of persons."""
        return len(self.persons)
    
    @strawberry.field
    async def estimated_cost(self, info) -> Optional[float]:
        """Estimated execution cost based on LLM usage."""
        # TODO: Calculate based on persons and their models
        return None

@strawberry.experimental.pydantic.type(model=PydanticExecutionState)
class ExecutionState:
    """Current state of a diagram execution."""
    id: ExecutionID
    status: strawberry.auto
    diagram_id: DiagramID
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
        return self.node_outputs if hasattr(self, 'node_outputs') else None
    
    @strawberry.field
    def variables(self) -> Optional[JSONScalar]:
        """Variables as JSON scalar."""
        return self.variables if hasattr(self, 'variables') else None
    
    @strawberry.field
    def duration_seconds(self) -> Optional[float]:
        """Execution duration in seconds."""
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None
    
    @strawberry.field
    def is_active(self) -> bool:
        """Whether execution is still active."""
        return self.status in ['running', 'paused']

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
        return self.data if hasattr(self, 'data') else None
    
    @strawberry.field
    def formatted_message(self) -> str:
        """Human-readable event message."""
        # Format based on event type
        if self.event_type == 'node_started':
            return f"Node {self.node_id} started"
        elif self.event_type == 'node_completed':
            return f"Node {self.node_id} completed"
        elif self.event_type == 'node_failed':
            return f"Node {self.node_id} failed"
        else:
            return f"{self.event_type} for node {self.node_id}"

# Note: Enums are handled by Pydantic models directly, no need to import from .enums