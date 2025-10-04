"""
Auto-generated unified node model for sub_diagram.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-10-04T16:50:38.731030
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType

from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class SubDiagramNode(BaseModel):
    """Execute another diagram as a node within the current diagram

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
    type: NodeType = Field(default=NodeType.SUB_DIAGRAM, frozen=True)

    # Optional node-specific fields
    
    diagram_name: Optional[str] = Field(default=None, description="Name of the diagram to execute (e.g., 'workflow/process')")
    
    diagram_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Inline diagram data (alternative to diagram_name)")
    
    input_mapping: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Map node inputs to sub-diagram variables")
    
    output_mapping: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Map sub-diagram outputs to node outputs")
    
    timeout: Optional[int] = Field(default=None, description="Execution timeout in seconds")
    
    wait_for_completion: bool = Field(default=True, description="Whether to wait for sub-diagram completion")
    
    isolate_conversation: bool = Field(default=False, description="Create isolated conversation context for sub-diagram")
    
    ignore_if_sub: bool = Field(default=False, alias="ignoreIfSub", description="Skip execution if this diagram is being run as a sub-diagram")
    
    diagram_format: Optional[DiagramFormat] = Field(default=None, description="Format of the diagram file (yaml, json, or light)")
    
    batch: bool = Field(default=False, description="Execute sub-diagram in batch mode for multiple inputs")
    
    batch_input_key: str = Field(default="items", description="Key in inputs containing the array of items for batch processing")
    
    batch_parallel: bool = Field(default=True, description="Execute batch items in parallel")

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
        data["diagram_name"] = self.diagram_name
        data["diagram_data"] = self.diagram_data
        data["input_mapping"] = self.input_mapping
        data["output_mapping"] = self.output_mapping
        data["timeout"] = self.timeout
        data["wait_for_completion"] = self.wait_for_completion
        data["isolate_conversation"] = self.isolate_conversation
        # Use original field name for compatibility
        data["ignoreIfSub"] = getattr(self, "ignore_if_sub")
        data["diagram_format"] = self.diagram_format
        data["batch"] = self.batch
        data["batch_input_key"] = self.batch_input_key
        data["batch_parallel"] = self.batch_parallel

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubDiagramNode":
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
        if not isinstance(other, SubDiagramNode):
            return False
        return self.id == other.id
