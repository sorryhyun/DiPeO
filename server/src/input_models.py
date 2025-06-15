"""Pydantic models for GraphQL input types."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
import base64

from server.src.domain import (
    NodeType, HandleDirection, DataType, LLMService, 
    ForgettingMode, ExecutionStatus
)


class Vec2Input(BaseModel):
    """2D position input."""
    x: float
    y: float
    
    model_config = ConfigDict(frozen=True)


class CreateNodeInput(BaseModel):
    """Input for creating a new node."""
    type: NodeType
    position: Vec2Input
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node-specific properties")
    
    @field_validator('label')
    @classmethod
    def validate_label(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Label cannot be empty")
        return v.strip()


class UpdateNodeInput(BaseModel):
    """Input for updating a node."""
    id: str
    position: Optional[Vec2Input] = None
    label: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    
    @field_validator('label')
    @classmethod
    def validate_label(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Label cannot be empty")
        return v.strip() if v else None


class CreateHandleInput(BaseModel):
    """Input for creating a handle."""
    node_id: str
    label: str
    direction: HandleDirection
    data_type: DataType = DataType.ANY
    position: Optional[Vec2Input] = None
    max_connections: Optional[int] = Field(None, ge=1)
    
    @field_validator('label')
    @classmethod
    def validate_label(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Label cannot be empty")
        return v.strip()


class CreateArrowInput(BaseModel):
    """Input for creating an arrow."""
    source: str  # HandleID
    target: str  # HandleID
    label: Optional[str] = None
    
    @field_validator('source', 'target')
    @classmethod
    def validate_handle_format(cls, v: str) -> str:
        if ':' not in v:
            raise ValueError("Handle ID must be in format 'nodeId:handleName'")
        return v


class CreatePersonInput(BaseModel):
    """Input for creating a person."""
    label: str
    service: LLMService
    model: str
    api_key_id: str
    system_prompt: Optional[str] = None
    forgetting_mode: ForgettingMode = ForgettingMode.NONE
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @field_validator('label')
    @classmethod
    def validate_label(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Label cannot be empty")
        return v.strip()
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Model cannot be empty")
        return v.strip()


class UpdatePersonInput(BaseModel):
    """Input for updating a person."""
    id: str
    label: Optional[str] = None
    model: Optional[str] = None
    api_key_id: Optional[str] = None
    system_prompt: Optional[str] = None
    forgetting_mode: Optional[ForgettingMode] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @field_validator('label', 'model')
    @classmethod
    def validate_non_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Value cannot be empty")
        return v.strip() if v else None


class CreateApiKeyInput(BaseModel):
    """Input for creating an API key."""
    label: str
    service: LLMService
    key: str
    
    @field_validator('label', 'key')
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Value cannot be empty")
        return v.strip()


class CreateDiagramInput(BaseModel):
    """Input for creating a new diagram."""
    name: str
    description: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> List[str]:
        if v is None:
            return []
        # Remove empty tags and duplicates
        cleaned_tags = [tag.strip() for tag in v if tag.strip()]
        return list(dict.fromkeys(cleaned_tags))  # Preserve order while removing duplicates


class ExecuteDiagramInput(BaseModel):
    """Input for executing a diagram."""
    diagram_id: str
    variables: Optional[Dict[str, Any]] = None
    debug_mode: bool = False
    timeout_seconds: Optional[int] = Field(None, gt=0, description="Execution timeout in seconds")
    max_iterations: Optional[int] = Field(None, gt=0, description="Maximum iterations for execution")


class ExecutionControlInput(BaseModel):
    """Input for controlling execution."""
    execution_id: str
    action: str  # pause, resume, abort, skip_node
    node_id: Optional[str] = None
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid_actions = {'pause', 'resume', 'abort', 'skip_node'}
        if v not in valid_actions:
            raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")
        return v


class InteractiveResponseInput(BaseModel):
    """Input for interactive response."""
    execution_id: str
    node_id: str
    response: str
    
    @field_validator('response')
    @classmethod
    def validate_response(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Response cannot be empty")
        return v


class DiagramFilterInput(BaseModel):
    """Filter for querying diagrams."""
    name_contains: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    modified_after: Optional[datetime] = None
    
    @field_validator('created_before')
    @classmethod
    def validate_created_before(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v and 'created_after' in info.data:
            created_after = info.data['created_after']
            if created_after and v <= created_after:
                raise ValueError("created_before must be after created_after")
        return v


class ExecutionFilterInput(BaseModel):
    """Filter for querying executions."""
    diagram_id: Optional[str] = None
    status: Optional[ExecutionStatus] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    active_only: bool = False
    
    @field_validator('started_before')
    @classmethod
    def validate_started_before(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v and 'started_after' in info.data:
            started_after = info.data['started_after']
            if started_after and v <= started_after:
                raise ValueError("started_before must be after started_after")
        return v


class FileUploadInput(BaseModel):
    """Input for file upload."""
    filename: str
    content_base64: str  # Base64 encoded file content
    content_type: Optional[str] = None
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Filename cannot be empty")
        # Basic filename validation
        invalid_chars = ['/', '\\', '\x00']
        for char in invalid_chars:
            if char in v:
                raise ValueError(f"Filename cannot contain '{char}'")
        return v.strip()
    
    @field_validator('content_base64')
    @classmethod
    def validate_base64(cls, v: str) -> str:
        try:
            # Verify it's valid base64
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("Invalid base64 content")
        return v
    
    def get_decoded_content(self) -> bytes:
        """Get the decoded file content."""
        return base64.b64decode(self.content_base64)


class ImportYamlInput(BaseModel):
    """Input for importing YAML diagram."""
    content: str  # YAML content as string
    filename: Optional[str] = None  # Optional filename to save as
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Filename cannot be empty")
            # Basic filename validation
            invalid_chars = ['/', '\\', '\x00']
            for char in invalid_chars:
                if char in v:
                    raise ValueError(f"Filename cannot contain '{char}'")
            return v.strip()
        return None