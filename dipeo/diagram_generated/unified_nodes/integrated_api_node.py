"""
Auto-generated unified node model for integrated_api.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-10-09T15:58:07.087581
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType


from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class IntegratedApiNode(BaseModel):
    """Connect to external APIs like Notion, Slack, GitHub, and more

    Unified model handling both validation and execution.
    """
    # Required base fields
    id: NodeID
    position: Vec2

    # Required node-specific fields
    provider: str = Field(description="API provider to connect to")
    operation: str = Field(description="Operation to perform (provider-specific)")

    # Optional base fields
    label: str = Field(default="", description="Node label for display")
    flipped: bool = Field(default=False, description="Whether handles are flipped")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    # Node type (constant for this node class)
    type: NodeType = Field(default=NodeType.INTEGRATED_API, frozen=True)

    # Optional node-specific fields
    
    resource_id: Optional[str] = Field(default=None, description="Resource identifier (e.g., page ID, channel ID)")
    
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Provider-specific configuration")
    
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    max_retries: float = Field(default=3, description="Maximum retry attempts")

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
        data["provider"] = self.provider
        data["operation"] = self.operation
        data["resource_id"] = self.resource_id
        data["config"] = self.config
        data["timeout"] = self.timeout
        data["max_retries"] = self.max_retries

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegratedApiNode":
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
        if not isinstance(other, IntegratedApiNode):
            return False
        return self.id == other.id
