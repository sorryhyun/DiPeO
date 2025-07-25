"""
Auto-generated static node type for endpoint.
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
class EndpointNode:
    """Exit point for diagram execution"""
    # Required base fields first
    id: NodeID
    position: Vec2
    
    # Required node-specific fields
    save_to_file: bool
    
    # Optional base fields
    label: str = ""
    flipped: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    # Node type (fixed for this node class)
    type: NodeType = field(default=NodeType.endpoint, init=False)
    
    # Optional node-specific fields
    file_name: str = ""

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
        data["save_to_file"] = self.save_to_file
        data["file_name"] = self.file_name
        return data