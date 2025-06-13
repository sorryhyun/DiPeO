"""Core domain types for DiPeO GraphQL schema."""
import strawberry
from typing import Optional, List, Dict, Any
from datetime import datetime

from .scalars import (
    NodeID, HandleID, ArrowID, PersonID, ApiKeyID, 
    ExecutionID, DiagramID
)
from .enums import (
    NodeType, HandleDirection, DataType, LLMService, 
    ForgettingMode, ExecutionStatus
)
from .node_data import NodeDataUnion

@strawberry.type
class Vec2:
    """2D position vector."""
    x: float
    y: float

@strawberry.type
class Handle:
    """Connection point on a node."""
    id: HandleID
    node_id: NodeID
    label: str
    direction: HandleDirection
    data_type: DataType
    position: Optional[Vec2] = None
    offset: Optional[Vec2] = None
    max_connections: Optional[int] = None

@strawberry.type
class ArrowData:
    """Additional data for an arrow."""
    label: Optional[str] = None
    loop_count: Optional[int] = None

@strawberry.type
class Arrow:
    """Connection between two handles."""
    id: ArrowID
    source: HandleID
    target: HandleID
    data: Optional[ArrowData] = None

@strawberry.type
class Node:
    """Node in a diagram."""
    id: NodeID
    type: NodeType
    position: Vec2
    data: NodeDataUnion
    
    @strawberry.field
    def display_name(self) -> str:
        """Computed display name for the node."""
        if hasattr(self.data, 'label'):
            return f"{self.type.value}: {self.data.label}"
        return self.type.value
    
    @strawberry.field
    async def handles(self, info) -> List[Handle]:
        """Get all handles for this node."""
        # This will be resolved from the diagram's handles
        diagram = info.context["diagram"]
        return [h for h in diagram.handles.values() if h.node_id == self.id]

@strawberry.type
class Person:
    """Person (LLM agent) configuration."""
    id: PersonID
    label: str
    service: LLMService
    model: str
    api_key_id: Optional[ApiKeyID] = None
    system_prompt: Optional[str] = None
    forgetting_mode: ForgettingMode = ForgettingMode.NONE
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    seed: Optional[int] = None
    
    @strawberry.field
    def masked_api_key(self) -> Optional[str]:
        """Return masked API key for display."""
        if not self.api_key_id:
            return None
        return f"****{str(self.api_key_id)[-4:]}"

@strawberry.type
class ApiKey:
    """API key configuration."""
    id: ApiKeyID
    label: str
    service: LLMService
    
    @strawberry.field
    def key(self, info) -> Optional[str]:
        """Actual key - requires permission."""
        # Check permission in resolver
        if info.context.get("can_read_api_keys"):
            return info.context["api_keys"].get(self.id)
        return None
    
    @strawberry.field
    def masked_key(self) -> str:
        """Masked version of the key."""
        return f"{self.service.value}-****"

@strawberry.type
class DiagramMetadata:
    """Metadata for a diagram."""
    id: Optional[DiagramID] = None
    name: Optional[str] = None
    description: Optional[str] = None
    version: str = "2.0.0"
    created: datetime
    modified: datetime
    author: Optional[str] = None
    tags: Optional[List[str]] = None

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
    node_outputs: Dict[str, Any]
    variables: Dict[str, Any]
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
    data: Dict[str, Any]
    
    @strawberry.field
    def formatted_message(self) -> str:
        """Human-readable event message."""
        if self.event_type == "node_completed":
            return f"Node {self.node_id} completed"
        elif self.event_type == "node_failed":
            return f"Node {self.node_id} failed: {self.data.get('error', 'Unknown error')}"
        return self.event_type.replace("_", " ").title()