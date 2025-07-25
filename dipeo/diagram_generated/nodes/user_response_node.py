"""
Auto-generated static node type for user_response.
DO NOT EDIT THIS FILE DIRECTLY.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, Literal

from dipeo.models.models import (
    NodeType, Vec2, NodeID, PersonID, MemoryConfig, MemorySettings, ToolConfig,
    HookTriggerMode, SupportedLanguage, HttpMethod, DBBlockSubType,
    NotionOperation, HookType, PersonLLMConfig, LLMService
)


@dataclass(frozen=True)
class UserResponseNode:
    """Collect user input"""
    # Required base fields first
    id: NodeID
    position: Vec2
    
    # Required node-specific fields
    prompt: str
    timeout: float
    
    # Optional base fields
    label: str = ""
    flipped: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    # Node type (fixed for this node class)
    type: NodeType = field(default=NodeType.user_response, init=False)
    
    # Optional node-specific fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = {
            "id": self.id,
            "type": self.type.value,
            "position": {"x": self.position.x, "y": self.position.y},
            "label": self.label,
            "flipped": self.flipped
        }
        if self.metadata:
            data["metadata"] = self.metadata
            
        # Add node-specific fields
        data["prompt"] = self.prompt
        data["timeout"] = self.timeout
        return data