"""
Auto-generated unified node model for template_job.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-10-06T11:12:06.460954
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType

from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class TemplateJobNode(BaseModel):
    """Process templates with data

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
    type: NodeType = Field(default=NodeType.TEMPLATE_JOB, frozen=True)

    # Optional node-specific fields
    
    template_path: Optional[str] = Field(default=None, description="Path to template file")
    
    template_content: Optional[str] = Field(default=None, description="Inline template content")
    
    output_path: Optional[str] = Field(default=None, description="Output file path")
    
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Variables configuration")
    
    engine: Literal["internal", "jinja2"] = Field(default="jinja2", description="Template engine to use")
    
    preprocessor: Optional[str] = Field(default=None, description="Preprocessor function to apply before templating")

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
        data["template_path"] = self.template_path
        data["template_content"] = self.template_content
        data["output_path"] = self.output_path
        data["variables"] = self.variables
        data["engine"] = self.engine
        data["preprocessor"] = self.preprocessor

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateJobNode":
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
        if not isinstance(other, TemplateJobNode):
            return False
        return self.id == other.id
