"""
Auto-generated unified node model for condition.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-09-18T13:14:40.928273
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType

from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class ConditionNode(BaseModel):
    """Conditional branching based on expressions

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
    type: NodeType = Field(default=NodeType.CONDITION, frozen=True)

    # Optional node-specific fields
    
    condition_type: Optional[Literal["detect_max_iterations", "check_nodes_executed", "custom", "llm_decision"]] = Field(default=None, description="Type of condition to evaluate")
    
    expression: Optional[str] = Field(default=None, description="Boolean expression to evaluate")
    
    node_indices: Optional[List[Any]] = Field(default_factory=list, description="Node indices for detect_max_iteration condition")
    
    person: Optional[str] = Field(default=None, description="AI agent to use for decision making")
    
    judge_by: Optional[str] = Field(default=None, description="Prompt for LLM to make a judgment")
    
    judge_by_file: Optional[str] = Field(default=None, description="External prompt file path")
    
    memorize_to: Optional[str] = Field(default=None, description="Memory control strategy (e.g., GOLDFISH for fresh evaluation)")
    
    at_most: Optional[float] = Field(default=None, description="Maximum messages to keep in memory")
    
    expose_index_as: Optional[str] = Field(default=None, description="Variable name to expose the condition node's execution count (0-based index) to downstream nodes")
    
    skippable: Optional[bool] = Field(default=None, description="When true, downstream nodes can execute even if this condition hasn't been evaluated yet")

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
        data["condition_type"] = self.condition_type
        data["expression"] = self.expression
        data["node_indices"] = self.node_indices
        data["person"] = self.person
        data["judge_by"] = self.judge_by
        data["judge_by_file"] = self.judge_by_file
        data["memorize_to"] = self.memorize_to
        data["at_most"] = self.at_most
        data["expose_index_as"] = self.expose_index_as
        data["skippable"] = self.skippable

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConditionNode":
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
        if not isinstance(other, ConditionNode):
            return False
        return self.id == other.id
