"""
Strawberry GraphQL types using Pydantic models as single source of truth.
This replaces the manual type definitions with automatic conversions.
"""
import strawberry
from typing import Optional, List

from ..types.scalars import JSONScalar, DiagramID, ExecutionID

# Import generated models
from src.__generated__.models import (
    DomainHandle, DomainNode, DomainArrow, DomainPerson,
    DomainApiKey, DiagramMetadata, DomainDiagram,
    ExecutionState as PydanticExecutionState,
    ExecutionEvent as PydanticExecutionEvent,
    Vec2 as PydanticVec2,
    DiagramFormat,
    TokenUsage as GeneratedTokenUsage
)

# No longer need domain-specific extensions - using generated model directly

# Convert basic types
# Use the models directly with strawberry.experimental.pydantic
@strawberry.experimental.pydantic.type(model=PydanticVec2, all_fields=True, description="2D position vector")
class Vec2:
    pass

@strawberry.experimental.pydantic.type(model=GeneratedTokenUsage, all_fields=True, description="Token usage statistics")
class TokenUsage:
    pass

# Convert domain models to Strawberry types
# Direct conversion for simple types
@strawberry.experimental.pydantic.type(model=DomainHandle, all_fields=True, description="Connection point on a node")
class DomainHandle:
    pass

@strawberry.experimental.pydantic.type(model=DomainNode)
class DomainNode:
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
    def handles(self, info) -> List[DomainHandle]:
        """Get handles associated with this node (virtual field for nested view)."""
        # Get handle_index from context if available
        handle_index = getattr(info.context, 'handle_index', None)
        if handle_index is None:
            return []
        
        # Return handles for this node from the index
        return handle_index.get(self.id, [])

@strawberry.experimental.pydantic.type(model=DomainArrow)
class DomainArrow:
    """Connection between two handles."""
    id: strawberry.auto
    source: strawberry.auto
    target: strawberry.auto
    
    @strawberry.field
    def data(self) -> Optional[JSONScalar]:
        """Arrow data as JSON scalar."""
        return self.data if hasattr(self, 'data') else None

@strawberry.experimental.pydantic.type(model=DomainPerson)
class DomainPerson:
    """Person (LLM agent) configuration."""
    id: strawberry.auto
    label: strawberry.auto
    service: strawberry.auto
    model: strawberry.auto
    api_key_id: strawberry.auto
    system_prompt: strawberry.auto
    forgetting_mode: strawberry.auto
    
    @strawberry.field
    def type(self) -> str:
        """Return the type as string."""
        return "person"
    
    @strawberry.field
    def masked_api_key(self) -> Optional[str]:
        """Return masked API key for display."""
        if not self.api_key_id:
            return None
        return f"****{str(self.api_key_id)[-4:]}"

@strawberry.experimental.pydantic.type(model=DomainApiKey)
class DomainApiKey:
    """API key configuration - excludes actual key."""
    id: strawberry.auto
    label: strawberry.auto
    service: strawberry.auto
    
    @strawberry.field
    def masked_key(self) -> str:
        """Masked version of the key."""
        return f"{self.service.value}-****"

# Metadata can be used directly
@strawberry.experimental.pydantic.type(model=DiagramMetadata, all_fields=True, description="Metadata for a diagram")
class DiagramMetadataType:
    pass

@strawberry.experimental.pydantic.type(model=DomainDiagram)
class DomainDiagramType:
    """Complete diagram with all components (backend format)."""
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

@strawberry.experimental.pydantic.type(
    model=PydanticExecutionState,
    fields=[
        "id",
        "status", 
        "diagram_id",
        "started_at",
        "ended_at",
        "running_nodes",
        "completed_nodes",
        "skipped_nodes",
        "paused_nodes",
        "failed_nodes",
        "token_usage",
        "error"
    ]
)
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
    token_usage: Optional[TokenUsage]
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