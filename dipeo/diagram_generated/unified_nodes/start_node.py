"""
Auto-generated unified node model for start.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-09-30T07:54:34.619766
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType

from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class StartNode(BaseModel):
    """Entry point for diagram execution

    Unified model handling both validation and execution.
    """
    # Required base fields
    id: NodeID
    position: Vec2

    # Required node-specific fields

    # Optional base fields
    label: str = Field(default="", description="Node label for display")
    flipped: bool = Field(default=False, description="Whether handles are flipped")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    # Node type (constant for this node class)
    type: NodeType = Field(default=NodeType.START, frozen=True)

    # Optional node-specific fields
    
    trigger_mode: Optional[HookTriggerMode] = Field(default=None, description="How this start node is triggered")
    
    custom_data: Optional[Any] = Field(default=None, description="Custom data to pass when manually triggered")
    
    output_data_structure: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Expected output data structure")
    
    hook_event: Optional[str] = Field(default=None, description="Event name to listen for")
    
    hook_filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Filters to apply to incoming events")

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
        data["trigger_mode"] = self.trigger_mode
        data["custom_data"] = self.custom_data
        data["output_data_structure"] = self.output_data_structure
        data["hook_event"] = self.hook_event
        data["hook_filters"] = self.hook_filters

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StartNode":
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
        if not isinstance(other, StartNode):
            return False
        return self.id == other.id
