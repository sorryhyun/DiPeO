"""
Auto-generated unified node model for person_job.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-09-21T17:46:48.401556
"""

from typing import *
from pydantic import BaseModel, Field, field_validator

from dipeo.domain.diagram.models.executable_diagram import BaseExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Vec2
from dipeo.diagram_generated.enums import NodeType

from dipeo.diagram_generated.domain_models import DomainPerson, PersonLLMConfig

from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class PersonJobNode(BaseModel):
    """Execute tasks using AI language models

    Unified model handling both validation and execution.
    """
    # Required base fields
    id: NodeID
    position: Vec2

    # Required node-specific fields
    max_iteration: int = Field(description="Maximum execution iterations")

    # Optional base fields
    label: str = Field(default="", description="Node label for display")
    flipped: bool = Field(default=False, description="Whether handles are flipped")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    # Node type (constant for this node class)
    type: NodeType = Field(default=NodeType.PERSON_JOB, frozen=True)

    # Optional node-specific fields
    
    person: Optional[str] = Field(default=None, description="AI person to use")
    
    first_only_prompt: Optional[str] = Field(default=None, description="Prompt used only on first execution")
    
    first_prompt_file: Optional[str] = Field(default=None, description="External prompt file for first iteration only")
    
    default_prompt: Optional[str] = Field(default=None, description="Default prompt template")
    
    prompt_file: Optional[str] = Field(default=None, description="Path to prompt file in /files/prompts/")
    
    memorize_to: Optional[str] = Field(default=None, description="Criteria used to select helpful messages for this task. Empty = memorize all. Special: 'GOLDFISH' for goldfish mode. Comma-separated for multiple criteria.")
    
    at_most: Optional[float] = Field(default=None, description="Select at most N messages to keep (system messages may be preserved in addition).")
    
    ignore_person: Optional[str] = Field(default=None, description="Comma-separated list of person IDs whose messages should be excluded from memory selection.")
    
    tools: Optional[List[ToolConfig]] = Field(default=None, description="Tools available to the AI agent")
    
    text_format: Optional[str] = Field(default=None, description="JSON schema or response format for structured outputs")
    
    text_format_file: Optional[str] = Field(default=None, description="Path to Python file containing Pydantic models for structured outputs")
    
    resolved_prompt: Optional[str] = Field(default=None, description="Pre-resolved prompt content from compile-time")
    
    resolved_first_prompt: Optional[str] = Field(default=None, description="Pre-resolved first prompt content from compile-time")
    
    batch: Optional[bool] = Field(default=None, description="Enable batch mode for processing multiple items")
    
    batch_input_key: Optional[str] = Field(default=None, description="Key containing the array to iterate over in batch mode")
    
    batch_parallel: Optional[bool] = Field(default=None, description="Execute batch items in parallel")
    
    max_concurrent: Optional[float] = Field(default=None, description="Maximum concurrent executions in batch mode")

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
        data["person"] = self.person
        data["first_only_prompt"] = self.first_only_prompt
        data["first_prompt_file"] = self.first_prompt_file
        data["default_prompt"] = self.default_prompt
        data["prompt_file"] = self.prompt_file
        data["max_iteration"] = self.max_iteration
        data["memorize_to"] = self.memorize_to
        data["at_most"] = self.at_most
        data["ignore_person"] = self.ignore_person
        data["tools"] = self.tools
        data["text_format"] = self.text_format
        data["text_format_file"] = self.text_format_file
        data["resolved_prompt"] = self.resolved_prompt
        data["resolved_first_prompt"] = self.resolved_first_prompt
        data["batch"] = self.batch
        data["batch_input_key"] = self.batch_input_key
        data["batch_parallel"] = self.batch_parallel
        data["max_concurrent"] = self.max_concurrent

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonJobNode":
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
        if not isinstance(other, PersonJobNode):
            return False
        return self.id == other.id
