"""
Auto-generated unified node model for diff_patch.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-09-30T20:07:54.674898
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType

from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class DiffPatchNode(BaseModel):
    """Apply unified diffs to files with safety controls

    Unified model handling both validation and execution.
    """
    # Required base fields
    id: NodeID
    position: Vec2

    # Required node-specific fields
    target_path: str = Field(description="Path to the file to patch")
    diff: str = Field(description="Unified diff content to apply")

    # Optional base fields
    label: str = Field(default="", description="Node label for display")
    flipped: bool = Field(default=False, description="Whether handles are flipped")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    # Node type (constant for this node class)
    type: NodeType = Field(default=NodeType.DIFF_PATCH, frozen=True)

    # Optional node-specific fields
    
    format: Optional[Literal["unified", "git", "context", "ed", "normal"]] = Field(default=None, description="Diff format type")
    
    apply_mode: Optional[Literal["normal", "force", "dry_run", "reverse"]] = Field(default=None, description="How to apply the patch")
    
    backup: Optional[bool] = Field(default=None, description="Create backup before patching")
    
    validate_patch: Optional[bool] = Field(default=None, description="Validate patch before applying")
    
    backup_dir: Optional[str] = Field(default=None, description="Directory for backup files")
    
    strip_level: Optional[float] = Field(default=None, description="Strip N leading path components (like patch -pN)")
    
    fuzz_factor: Optional[float] = Field(default=None, description="Number of lines that can be ignored when matching context")
    
    reject_file: Optional[str] = Field(default=None, description="Path to save rejected hunks")
    
    ignore_whitespace: Optional[bool] = Field(default=None, description="Ignore whitespace changes when matching")
    
    create_missing: Optional[bool] = Field(default=None, description="Create target file if it doesn't exist")

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
        data["target_path"] = self.target_path
        data["diff"] = self.diff
        data["format"] = self.format
        data["apply_mode"] = self.apply_mode
        data["backup"] = self.backup
        data["validate_patch"] = self.validate_patch
        data["backup_dir"] = self.backup_dir
        data["strip_level"] = self.strip_level
        data["fuzz_factor"] = self.fuzz_factor
        data["reject_file"] = self.reject_file
        data["ignore_whitespace"] = self.ignore_whitespace
        data["create_missing"] = self.create_missing

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiffPatchNode":
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
        if not isinstance(other, DiffPatchNode):
            return False
        return self.id == other.id
