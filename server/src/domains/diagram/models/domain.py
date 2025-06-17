"""
Enhanced domain models for GraphQL integration using Pydantic as single source of truth.
These models will be used with @strawberry.experimental.pydantic.type decorator.
"""
from typing import Dict, Optional, List, Any, Union, Final
from pydantic import BaseModel, Field, computed_field, ConfigDict
from datetime import datetime
from enum import Enum

# Import shared domain models
from src.shared.domain import (
    # Enums
    NodeType,
    HandleDirection,
    DataType,
    LLMService,
    ForgettingMode,
    DiagramFormat,
    ExecutionStatus,
    DBBlockSubType,
    ContentType,
    ContextCleaningRule,
    # Type aliases
    NodeID,
    ArrowID,
    HandleID,
    PersonID,
    ApiKeyID,
    DiagramID,
    ExecutionID,
    # Base models
    Vec2,
    # Constants
    API_BASE_PATH,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    SUPPORTED_DOC_EXTENSIONS,
    SUPPORTED_CODE_EXTENSIONS,
    SERVICE_TO_PROVIDER_MAP,
    PROVIDER_TO_ENUM_MAP,
    DEFAULT_SERVICE,
)

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
    api_key_id: Optional[ApiKeyID] = Field(None, alias="apiKeyId")
    systemPrompt: Optional[str] = None
    forgettingMode: ForgettingMode = ForgettingMode.NO_FORGET
    type: str = "person"
    
    model_config = ConfigDict(populate_by_name=True)
    
    @computed_field
    @property
    def masked_api_key(self) -> Optional[str]:
        """Return masked API key for display."""
        if not self.api_key_id:
            return None
        return f"****{str(self.api_key_id)[-4:]}"

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
    api_keys: Dict[ApiKeyID, DomainApiKey]
    metadata: Optional[DiagramMetadata] = None
    
    def to_graphql(self) -> DiagramForGraphQL:
        """Convert to GraphQL-friendly format with lists."""
        return DiagramForGraphQL(
            nodes=list(self.nodes.values()),
            handles=list(self.handles.values()),
            arrows=list(self.arrows.values()),
            persons=list(self.persons.values()),
            api_keys=list(self.api_keys.values()),
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
            api_keys={api_key.id: api_key for api_key in graphql_diagram.api_keys},
            metadata=graphql_diagram.metadata
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DomainDiagram':
        """Create DomainDiagram from dictionary (Pydantic v2 compatibility)."""
        return cls.model_validate(data)

# Execution-related models
class TokenUsage(BaseModel):
    """Token usage statistics."""
    input: int = 0
    output: int = 0
    cached: Optional[int] = 0
    
    @computed_field
    @property
    def total(self) -> int:
        """Total tokens used (input + output)"""
        return self.input + self.output
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return self.model_dump()
    
    @classmethod
    def from_response(cls, response: dict) -> 'TokenUsage':
        """Create TokenUsage from LLM response dict"""
        return cls(
            input=response.get("input_tokens", 0),
            output=response.get("output_tokens", 0),
            cached=response.get("cached_tokens", 0)
        )
    
    @classmethod
    def from_usage(cls, usage: Any, service: str = None) -> 'TokenUsage':
        """Create from provider-specific usage object"""
        if not usage:
            return cls()
        
        # Handle different provider formats
        if service == "gemini" and isinstance(usage, (list, tuple)):
            return cls(
                input=usage[0] if len(usage) > 0 else 0,
                output=usage[1] if len(usage) > 1 else 0
            )
        
        # Extract tokens based on format
        input_tokens = (getattr(usage, 'input_tokens', None) or
                        getattr(usage, 'prompt_tokens', None) or 0)
        output_tokens = (getattr(usage, 'output_tokens', None) or
                         getattr(usage, 'completion_tokens', None) or 0)
        cached_tokens = 0
        
        # Special handling for OpenAI cached tokens
        if service == "openai":
            # Try to get cached tokens from nested structure
            if hasattr(usage, 'input_tokens_details') and hasattr(usage.input_tokens_details, 'cached_tokens'):
                cached_tokens = usage.input_tokens_details.cached_tokens or 0
        else:
            cached_tokens = getattr(usage, 'cached_tokens', 0)
            
        return cls(
            input=input_tokens,
            output=output_tokens,
            cached=cached_tokens
        )

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

# Constants are now imported from shared.domain.constants