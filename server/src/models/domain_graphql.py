"""
Enhanced domain models for GraphQL integration using Pydantic as single source of truth.
These models will be used with @strawberry.experimental.pydantic.type decorator.
"""
from typing import Dict, Optional, List, Any, Union
from pydantic import BaseModel, Field, computed_field
from datetime import datetime
from enum import Enum

# Import enums to use as Pydantic enums
class NodeType(str, Enum):
    START = "start"
    PERSON_JOB = "person_job"
    CONDITION = "condition"
    JOB = "job"
    ENDPOINT = "endpoint"
    DB = "db"
    USER_RESPONSE = "user_response"
    NOTION = "notion"
    PERSON_BATCH_JOB = "person_batch_job"

class HandleDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    # Map legacy values
    IN = "in"
    OUT = "out"
    
    @classmethod
    def _missing_(cls, value):
        """Handle legacy values."""
        if value == "in":
            return cls.INPUT
        elif value == "out":
            return cls.OUTPUT
        return None

class DataType(str, Enum):
    ANY = "any"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"

class LLMService(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    BEDROCK = "bedrock"
    VERTEX = "vertex"
    DEEPSEEK = "deepseek"
    # Map legacy values
    CLAUDE = "claude"
    GEMINI = "gemini"
    GROK = "grok"
    
    @classmethod
    def _missing_(cls, value):
        """Handle legacy values."""
        if value == "claude":
            return cls.ANTHROPIC
        elif value == "gemini":
            return cls.GOOGLE
        elif value == "grok":
            return cls.GROQ
        return None

class ForgettingMode(str, Enum):
    NO_FORGET = "no_forget"
    NONE = "none"
    ON_EVERY_TURN = "on_every_turn"
    UPON_REQUEST = "upon_request"
    
    @classmethod
    def _missing_(cls, value):
        """Handle legacy values."""
        if value == "no_forget":
            return cls.NONE
        return None

class ExecutionStatus(str, Enum):
    STARTED = "started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"

# Type aliases
NodeID = str
ArrowID = str
HandleID = str
PersonID = str
ApiKeyID = str
DiagramID = str
ExecutionID = str

# Basic types for GraphQL
class Vec2(BaseModel):
    """2D position vector."""
    x: float
    y: float

# Enhanced domain models with computed fields for GraphQL
class DomainHandle(BaseModel):
    """Connection point on a node."""
    id: HandleID
    nodeId: NodeID
    label: str
    direction: HandleDirection
    dataType: DataType = DataType.ANY
    position: Optional[str] = None  # "left" | "right" | "top" | "bottom"

class DomainNode(BaseModel):
    """Node in a diagram."""
    id: NodeID
    type: NodeType
    position: Vec2
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @computed_field
    @property
    def display_name(self) -> str:
        """Computed display name for the node."""
        if 'label' in self.data:
            return f"{self.type.value}: {self.data['label']}"
        return self.type.value

class DomainArrow(BaseModel):
    """Connection between two handles."""
    id: ArrowID
    source: HandleID  # "nodeId:handleName" format
    target: HandleID  # "nodeId:handleName" format
    data: Optional[Dict[str, Any]] = None

class DomainPerson(BaseModel):
    """Person (LLM agent) configuration."""
    id: PersonID
    label: str
    service: LLMService
    model: str
    apiKeyId: ApiKeyID
    systemPrompt: Optional[str] = None
    forgettingMode: ForgettingMode = ForgettingMode.NO_FORGET
    type: str = "person"
    
    @computed_field
    @property
    def masked_api_key(self) -> Optional[str]:
        """Return masked API key for display."""
        if not self.apiKeyId:
            return None
        return f"****{str(self.apiKeyId)[-4:]}"

class DomainApiKey(BaseModel):
    """API key configuration."""
    id: ApiKeyID
    label: str
    service: LLMService
    key: str = Field(exclude=True)  # Exclude from serialization by default
    
    @computed_field
    @property
    def masked_key(self) -> str:
        """Masked version of the key."""
        return f"{self.service.value}-****"

class DiagramMetadata(BaseModel):
    """Metadata for a diagram."""
    id: Optional[DiagramID] = None
    name: Optional[str] = None
    description: Optional[str] = None
    version: str = "2.0.0"
    created: datetime = Field(default_factory=datetime.now)
    modified: datetime = Field(default_factory=datetime.now)
    author: Optional[str] = None
    tags: Optional[List[str]] = None

# For GraphQL, we'll create separate list-based versions
class DiagramForGraphQL(BaseModel):
    """Diagram structure optimized for GraphQL with lists instead of dicts."""
    nodes: List[DomainNode]
    handles: List[DomainHandle]
    arrows: List[DomainArrow]
    persons: List[DomainPerson]
    api_keys: List[DomainApiKey]
    metadata: Optional[DiagramMetadata] = None
    
    @computed_field
    @property
    def node_count(self) -> int:
        """Total number of nodes."""
        return len(self.nodes)
    
    @computed_field
    @property
    def arrow_count(self) -> int:
        """Total number of arrows."""
        return len(self.arrows)
    
    @computed_field
    @property
    def person_count(self) -> int:
        """Total number of persons."""
        return len(self.persons)

# Keep the original domain model for internal use
class DomainDiagram(BaseModel):
    """Main diagram model with dictionaries (internal format)."""
    nodes: Dict[NodeID, DomainNode]
    handles: Dict[HandleID, DomainHandle]
    arrows: Dict[ArrowID, DomainArrow]
    persons: Dict[PersonID, DomainPerson]
    apiKeys: Dict[ApiKeyID, DomainApiKey]
    metadata: Optional[DiagramMetadata] = None
    
    def to_graphql(self) -> DiagramForGraphQL:
        """Convert to GraphQL-friendly format with lists."""
        return DiagramForGraphQL(
            nodes=list(self.nodes.values()),
            handles=list(self.handles.values()),
            arrows=list(self.arrows.values()),
            persons=list(self.persons.values()),
            api_keys=list(self.apiKeys.values()),
            metadata=self.metadata
        )
    
    @classmethod
    def from_graphql(cls, graphql_diagram: DiagramForGraphQL) -> 'DomainDiagram':
        """Convert from GraphQL format back to domain format."""
        return cls(
            nodes={node.id: node for node in graphql_diagram.nodes},
            handles={handle.id: handle for handle in graphql_diagram.handles},
            arrows={arrow.id: arrow for arrow in graphql_diagram.arrows},
            persons={person.id: person for person in graphql_diagram.persons},
            apiKeys={api_key.id: api_key for api_key in graphql_diagram.api_keys},
            metadata=graphql_diagram.metadata
        )

# Execution-related models
class TokenUsage(BaseModel):
    """Token usage statistics."""
    input: int
    output: int
    cached: Optional[int] = None
    total: int

class ExecutionState(BaseModel):
    """Current state of a diagram execution."""
    id: ExecutionID
    status: ExecutionStatus
    diagram_id: Optional[DiagramID]
    started_at: datetime
    ended_at: Optional[datetime] = None
    running_nodes: List[NodeID] = Field(default_factory=list)
    completed_nodes: List[NodeID] = Field(default_factory=list)
    skipped_nodes: List[NodeID] = Field(default_factory=list)
    paused_nodes: List[NodeID] = Field(default_factory=list)
    failed_nodes: List[NodeID] = Field(default_factory=list)
    node_outputs: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    token_usage: Optional[TokenUsage] = None
    error: Optional[str] = None
    
    @computed_field
    @property
    def duration_seconds(self) -> Optional[float]:
        """Execution duration in seconds."""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None
    
    @computed_field
    @property
    def is_active(self) -> bool:
        """Whether execution is still active."""
        return self.status in [
            ExecutionStatus.STARTED, 
            ExecutionStatus.RUNNING, 
            ExecutionStatus.PAUSED
        ]

class ExecutionEvent(BaseModel):
    """Event during diagram execution."""
    execution_id: ExecutionID
    sequence: int
    event_type: str
    node_id: Optional[NodeID] = None
    timestamp: datetime
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @computed_field
    @property
    def formatted_message(self) -> str:
        """Human-readable event message."""
        if self.event_type == "node_completed":
            return f"Node {self.node_id} completed"
        elif self.event_type == "node_failed":
            error = self.data.get('error', 'Unknown error') if isinstance(self.data, dict) else 'Unknown error'
            return f"Node {self.node_id} failed: {error}"
        return self.event_type.replace("_", " ").title()