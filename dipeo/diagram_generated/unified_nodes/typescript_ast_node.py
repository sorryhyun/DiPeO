"""
Auto-generated unified node model for typescript_ast.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-09-30T20:07:55.049685
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType

from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class TypescriptAstNode(BaseModel):
    """Parses TypeScript source code and extracts AST, interfaces, types, and enums

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
    type: NodeType = Field(default=NodeType.TYPESCRIPT_AST, frozen=True)

    # Optional node-specific fields
    
    source: Optional[str] = Field(default=None, description="TypeScript source code to parse")
    
    extract_patterns: Optional[List[Any]] = Field(default_factory=list, alias="extractPatterns", description="Patterns to extract from the AST")
    
    include_js_doc: Optional[bool] = Field(default=None, alias="includeJSDoc", description="Include JSDoc comments in the extracted data")
    
    parse_mode: Optional[Literal["module", "script"]] = Field(default=None, alias="parseMode", description="TypeScript parsing mode")
    
    transform_enums: Optional[bool] = Field(default=None, alias="transformEnums", description="Transform enum definitions to a simpler format")
    
    flatten_output: Optional[bool] = Field(default=None, alias="flattenOutput", description="Flatten the output structure for easier consumption")
    
    output_format: Optional[Literal["standard", "for_codegen", "for_analysis"]] = Field(default=None, alias="outputFormat", description="Output format for the parsed data")
    
    batch: Optional[bool] = Field(default=None, description="Enable batch processing mode")
    
    batch_input_key: Optional[str] = Field(default=None, alias="batchInputKey", description="Key to extract batch items from input")

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
        data["source"] = self.source
        # Use original field name for compatibility
        data["extractPatterns"] = getattr(self, "extract_patterns")
        # Use original field name for compatibility
        data["includeJSDoc"] = getattr(self, "include_js_doc")
        # Use original field name for compatibility
        data["parseMode"] = getattr(self, "parse_mode")
        # Use original field name for compatibility
        data["transformEnums"] = getattr(self, "transform_enums")
        # Use original field name for compatibility
        data["flattenOutput"] = getattr(self, "flatten_output")
        # Use original field name for compatibility
        data["outputFormat"] = getattr(self, "output_format")
        data["batch"] = self.batch
        # Use original field name for compatibility
        data["batchInputKey"] = getattr(self, "batch_input_key")

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TypescriptAstNode":
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
        if not isinstance(other, TypescriptAstNode):
            return False
        return self.id == other.id
