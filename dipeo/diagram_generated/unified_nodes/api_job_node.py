"""
Auto-generated unified node model for api_job.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-10-19T16:24:22.538850
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType


from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class ApiJobNode(BaseModel):
    """Make HTTP API requests

    Unified model handling both validation and execution.
    """
    # Required base fields
    id: NodeID
    position: Vec2

    # Required node-specific fields
    url: str = Field(description="API endpoint URL")
    method: HttpMethod = Field(description="HTTP method")

    # Optional base fields
    label: str = Field(default="", description="Node label for display")
    flipped: bool = Field(default=False, description="Whether handles are flipped")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    # Node type (constant for this node class)
    type: NodeType = Field(default=NodeType.API_JOB, frozen=True)

    # Optional node-specific fields
    
    headers: Optional[Dict[str, Any]] = Field(default_factory=dict, description="HTTP headers")
    
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Query parameters")
    
    body: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Request body")
    
    timeout: Optional[int] = Field(default=None, description="Request timeout in seconds")
    
    auth_type: Optional[Literal["none", "bearer", "basic", "api_key"]] = Field(default=None, description="Authentication type")
    
    auth_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Authentication configuration")

    class Config:
        # Make the instance immutable after creation
        frozen = True
        # Forbid extra fields
        extra = "forbid"
        # Use enum values for JSON serialization
        use_enum_values = False
        # Allow field aliases for camelCase compatibility
        populate_by_name = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation for serialization."""
        data = {
            "id": self.id,
            "type": self.type.value if hasattr(self.type, 'value') else self.type,
            "position": {"x": self.position.x, "y": self.position.y},
            "label": self.label,
            "flipped": self.flipped
        }
        if self.metadata:
            data["metadata"] = self.metadata

        # Add node-specific fields using original names
        data["url"] = self.url
        data["method"] = self.method
        data["headers"] = self.headers
        data["params"] = self.params
        data["body"] = self.body
        data["timeout"] = self.timeout
        data["auth_type"] = self.auth_type
        data["auth_config"] = self.auth_config

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApiJobNode":
        """Create node from dictionary representation.

        Handles both camelCase (from JSON/GraphQL) and snake_case (internal) field names.
        """
        # Convert position if needed
        if "position" in data and isinstance(data["position"], dict):
            data["position"] = Vec2(x=data["position"]["x"], y=data["position"]["y"])

        # The Pydantic model will handle field aliasing automatically
        return cls(**data)

    def __hash__(self) -> int:
        """Make the node hashable for use in sets/dicts."""
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        """Equality based on node ID."""
        if not isinstance(other, ApiJobNode):
            return False
        return self.id == other.id
