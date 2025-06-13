"""Input types for GraphQL mutations."""
import strawberry
from typing import Optional, List
from datetime import datetime

from .scalars import (
    NodeID, HandleID, ArrowID, PersonID, ApiKeyID, 
    DiagramID, ExecutionID, JSONScalar
)
from .enums import (
    NodeType, HandleDirection, DataType, LLMService, 
    ForgettingMode, ExecutionStatus
)

@strawberry.input
class Vec2Input:
    """2D position input."""
    x: float
    y: float

@strawberry.input
class CreateNodeInput:
    """Input for creating a new node."""
    type: NodeType
    position: Vec2Input
    label: str
    properties: JSONScalar  # Node-specific properties

@strawberry.input
class UpdateNodeInput:
    """Input for updating a node."""
    id: NodeID
    position: Optional[Vec2Input] = None
    label: Optional[str] = None
    properties: Optional[JSONScalar] = None

@strawberry.input
class CreateHandleInput:
    """Input for creating a handle."""
    node_id: NodeID
    label: str
    direction: HandleDirection
    data_type: DataType = DataType.ANY
    position: Optional[Vec2Input] = None
    max_connections: Optional[int] = None

@strawberry.input
class CreateArrowInput:
    """Input for creating an arrow."""
    source: HandleID
    target: HandleID
    label: Optional[str] = None

@strawberry.input
class CreatePersonInput:
    """Input for creating a person."""
    label: str
    service: LLMService
    model: str
    api_key_id: ApiKeyID
    system_prompt: Optional[str] = None
    forgetting_mode: ForgettingMode = ForgettingMode.NONE
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None

@strawberry.input
class UpdatePersonInput:
    """Input for updating a person."""
    id: PersonID
    label: Optional[str] = None
    model: Optional[str] = None
    api_key_id: Optional[ApiKeyID] = None
    system_prompt: Optional[str] = None
    forgetting_mode: Optional[ForgettingMode] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

@strawberry.input
class CreateApiKeyInput:
    """Input for creating an API key."""
    label: str
    service: LLMService
    key: str

@strawberry.input
class CreateDiagramInput:
    """Input for creating a new diagram."""
    name: str
    description: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None

@strawberry.input
class ExecuteDiagramInput:
    """Input for executing a diagram."""
    diagram_id: DiagramID
    variables: Optional[JSONScalar] = None
    debug_mode: bool = False
    timeout: Optional[int] = None
    max_iterations: Optional[int] = None

@strawberry.input
class ExecutionControlInput:
    """Input for controlling execution."""
    execution_id: ExecutionID
    action: str  # pause, resume, abort, skip_node
    node_id: Optional[NodeID] = None

@strawberry.input
class InteractiveResponseInput:
    """Input for interactive response."""
    execution_id: ExecutionID
    node_id: NodeID
    response: str

@strawberry.input
class DiagramFilterInput:
    """Filter for querying diagrams."""
    name_contains: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    modified_after: Optional[datetime] = None

@strawberry.input
class ExecutionFilterInput:
    """Filter for querying executions."""
    diagram_id: Optional[DiagramID] = None
    status: Optional[ExecutionStatus] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    active_only: bool = False

@strawberry.input
class FileUploadInput:
    """Input for file upload."""
    filename: str
    content_base64: str  # Base64 encoded file content
    content_type: Optional[str] = None

@strawberry.input
class ImportYamlInput:
    """Input for importing YAML diagram."""
    content: str  # YAML content as string
    filename: Optional[str] = None  # Optional filename to save as