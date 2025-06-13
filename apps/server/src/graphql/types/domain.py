"""Strawberry GraphQL types based on existing Pydantic domain models."""
import strawberry
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...models.domain import (
    DomainHandle, DomainNode, DomainArrow, DomainPerson, 
    DomainApiKey, DiagramMetadata, DomainDiagram
)
from .scalars import (
    NodeID, HandleID, ArrowID, PersonID, ApiKeyID, 
    ExecutionID, DiagramID, JSONScalar
)
from .enums import (
    NodeType, HandleDirection, DataType, LLMService, 
    ForgettingMode, ExecutionStatus
)


# Basic types
@strawberry.type
class Vec2:
    """2D position vector."""
    x: float
    y: float


@strawberry.type
class ArrowData:
    """Additional data for an arrow."""
    label: Optional[str] = None
    loop_count: Optional[int] = None


# Convert Pydantic models to Strawberry types
@strawberry.experimental.pydantic.type(model=DomainHandle)
class Handle:
    """Connection point on a node."""
    id: strawberry.auto
    nodeId: strawberry.auto
    label: strawberry.auto
    direction: strawberry.auto
    dataType: strawberry.auto
    # position is a string ("left", "right", "top", "bottom") in the domain model
    # but GraphQL expects Optional[Vec2]. We'll expose it as a string for now.
    position: Optional[str] = strawberry.auto


@strawberry.experimental.pydantic.type(model=DomainNode)
class Node:
    """Node in a diagram."""
    id: strawberry.auto
    type: strawberry.auto
    data: JSONScalar
    
    @strawberry.field
    def position(self) -> Vec2:
        """Node position as Vec2."""
        pos_dict = self.__pydantic_model__.position
        return Vec2(x=pos_dict['x'], y=pos_dict['y'])
    
    @strawberry.field
    def display_name(self) -> str:
        """Computed display name for the node."""
        if 'label' in self.data:
            return f"{self.type}: {self.data['label']}"
        return self.type


@strawberry.experimental.pydantic.type(model=DomainArrow)
class Arrow:
    """Connection between two handles."""
    id: strawberry.auto
    source: strawberry.auto
    target: strawberry.auto
    data: Optional[JSONScalar] = strawberry.auto


@strawberry.experimental.pydantic.type(model=DomainPerson, all_fields=True)
class Person:
    """Person (LLM agent) configuration."""
    
    @strawberry.field
    def masked_api_key(self) -> Optional[str]:
        """Return masked API key for display."""
        if not self.apiKeyId:
            return None
        return f"****{str(self.apiKeyId)[-4:]}"


@strawberry.experimental.pydantic.type(model=DomainApiKey)
class ApiKey:
    """API key configuration."""
    id: strawberry.auto
    label: strawberry.auto
    service: strawberry.auto
    # Don't expose the actual key by default
    
    @strawberry.field
    def masked_key(self) -> str:
        """Masked version of the key."""
        return f"{self.service}-****"


@strawberry.experimental.pydantic.type(model=DiagramMetadata, all_fields=True)
class DiagramMetadata:
    """Metadata for a diagram."""
    pass


@strawberry.type
class Diagram:
    """Complete diagram with all components."""
    nodes: List[Node]
    handles: List[Handle]
    arrows: List[Arrow]
    persons: List[Person]
    api_keys: List[ApiKey]
    metadata: Optional[DiagramMetadata] = None
    
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
        # This would calculate based on persons and their models
        # Placeholder for now
        return None


# Execution-related types (not in domain.py, so we define them here)
@strawberry.type
class TokenUsage:
    """Token usage statistics."""
    input: int
    output: int
    cached: Optional[int] = None
    total: int


@strawberry.type
class ExecutionState:
    """Current state of a diagram execution."""
    id: ExecutionID
    status: ExecutionStatus
    diagram_id: Optional[DiagramID]
    started_at: datetime
    ended_at: Optional[datetime] = None
    running_nodes: List[NodeID]
    completed_nodes: List[NodeID]
    skipped_nodes: List[NodeID]
    paused_nodes: List[NodeID]
    failed_nodes: List[NodeID]
    node_outputs: JSONScalar
    variables: JSONScalar
    token_usage: Optional[TokenUsage] = None
    error: Optional[str] = None
    
    @strawberry.field
    def duration_seconds(self) -> Optional[float]:
        """Execution duration in seconds."""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None
    
    @strawberry.field
    def is_active(self) -> bool:
        """Whether execution is still active."""
        return self.status in [
            ExecutionStatus.STARTED, 
            ExecutionStatus.RUNNING, 
            ExecutionStatus.PAUSED
        ]


@strawberry.type
class ExecutionEvent:
    """Event during diagram execution."""
    execution_id: ExecutionID
    sequence: int
    event_type: str
    node_id: Optional[NodeID] = None
    timestamp: datetime
    data: JSONScalar
    
    @strawberry.field
    def formatted_message(self) -> str:
        """Human-readable event message."""
        if self.event_type == "node_completed":
            return f"Node {self.node_id} completed"
        elif self.event_type == "node_failed":
            error = self.data.get('error', 'Unknown error') if isinstance(self.data, dict) else 'Unknown error'
            return f"Node {self.node_id} failed: {error}"
        return self.event_type.replace("_", " ").title()