"""
Auto-generated unified node model for ir_builder.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-09-19T17:20:54.262502
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType

from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class IrBuilderNode(BaseModel):
    """Build Intermediate Representation for code generation

    Unified model handling both validation and execution.
    """
    # Required base fields
    id: NodeID
    position: Vec2

    # Required node-specific fields
    builder_type: Literal["backend", "frontend", "strawberry", "custom"] = Field(description="Type of IR builder to use")

    # Optional base fields
    label: str = Field(default="", description="Node label for display")
    flipped: bool = Field(default=False, description="Whether handles are flipped")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    # Node type (constant for this node class)
    type: NodeType = Field(default=NodeType.IR_BUILDER, frozen=True)

    # Optional node-specific fields
    
    source_type: Optional[Literal["ast", "schema", "config", "auto"]] = Field(default=None, description="Type of source data")
    
    config_path: Optional[str] = Field(default=None, description="Path to configuration directory")
    
    output_format: Optional[Literal["json", "yaml", "python"]] = Field(default=None, description="Output format for IR")
    
    cache_enabled: Optional[bool] = Field(default=None, description="Enable IR caching")
    
    validate_output: Optional[bool] = Field(default=None, description="Validate IR structure before output")

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
        data["builder_type"] = self.builder_type
        data["source_type"] = self.source_type
        data["config_path"] = self.config_path
        data["output_format"] = self.output_format
        data["cache_enabled"] = self.cache_enabled
        data["validate_output"] = self.validate_output

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IrBuilderNode":
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
        if not isinstance(other, IrBuilderNode):
            return False
        return self.id == other.id
