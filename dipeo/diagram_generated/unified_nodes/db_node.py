"""
Auto-generated unified node model for db.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-10-09T15:58:07.084943
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType


from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class DbNode(BaseModel):
    """Database operations

    Unified model handling both validation and execution.
    """
    # Required base fields
    id: NodeID
    position: Vec2

    # Required node-specific fields
    sub_type: DBBlockSubType = Field(description="Database operation type")
    operation: Literal["prompt", "read", "write", "append", "update"] = Field(description="Operation configuration")

    # Optional base fields
    label: str = Field(default="", description="Node label for display")
    flipped: bool = Field(default=False, description="Whether handles are flipped")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    # Node type (constant for this node class)
    type: NodeType = Field(default=NodeType.DB, frozen=True)

    # Optional node-specific fields
    
    file: Optional[Any] = Field(default=None, description="File path or array of file paths")
    
    collection: Optional[str] = Field(default=None, description="Database collection name")
    
    query: Optional[str] = Field(default=None, description="Query configuration")
    
    keys: Optional[Any] = Field(default=None, description="Single key or list of dot-separated keys to target within the JSON payload")
    
    lines: Optional[Any] = Field(default=None, description="Line selection or ranges to read (e.g., 1:120 or ['10:20'])")
    
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Data configuration")
    
    format: Literal["json", "yaml", "csv", "text", "xml"] = Field(default="json", description="Data format (json, yaml, csv, text, etc.)")

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
        data["file"] = self.file
        data["collection"] = self.collection
        data["sub_type"] = self.sub_type
        data["operation"] = self.operation
        data["query"] = self.query
        data["keys"] = self.keys
        data["lines"] = self.lines
        data["data"] = self.data
        data["format"] = self.format

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DbNode":
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
        if not isinstance(other, DbNode):
            return False
        return self.id == other.id
