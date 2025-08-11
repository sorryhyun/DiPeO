"""Format-specific Pydantic models for type-safe diagram handling.

These models provide strong typing for different diagram formats while
maintaining compatibility with the base DomainDiagram model.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from dipeo.diagram_generated import (
    DomainDiagram,
    DomainNode,
    DomainArrow,
    DomainHandle,
    DomainPerson,
    DiagramMetadata,
    NodeID,
    HandleID,
    PersonID,
)


class LightNode(BaseModel):
    """Light format node representation."""
    type: str
    label: Optional[str] = None
    position: Optional[Dict[str, int]] = None
    # All other properties go here as flat structure
    model_config = {"extra": "allow"}  # Allow additional fields
    
    @field_validator("position")
    def validate_position(cls, v):
        if v and not all(k in v for k in ["x", "y"]):
            raise ValueError("Position must have x and y coordinates")
        return v


class LightConnection(BaseModel):
    """Light format connection representation."""
    from_: str = Field(alias="from")
    to: str
    label: Optional[str] = None
    type: Optional[str] = None
    # Additional connection properties
    model_config = {"extra": "allow"}


class LightDiagram(BaseModel):
    """Light format diagram with simplified structure.
    
    This format uses labels for references and has a flatter structure
    suitable for human editing in YAML.
    """
    nodes: List[LightNode]
    connections: List[LightConnection]
    persons: Optional[List[Dict[str, Any]]] = None
    api_keys: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class ReadableNode(BaseModel):
    """Readable format node with explicit structure."""
    id: str
    type: str
    label: Optional[str] = None
    position: Dict[str, int]
    props: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("position")
    def validate_position(cls, v):
        if not all(k in v for k in ["x", "y"]):
            raise ValueError("Position must have x and y coordinates")
        return v


class ReadableArrow(BaseModel):
    """Readable format arrow with explicit IDs."""
    id: str
    source: str
    target: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    label: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ReadableDiagram(BaseModel):
    """Readable format diagram with explicit IDs and structure.
    
    This format is more verbose but clearer for understanding
    the complete diagram structure.
    """
    version: str = "readable"
    nodes: List[ReadableNode]
    arrows: List[ReadableArrow]
    persons: Optional[List[Dict[str, Any]]] = None
    api_keys: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class NativeDiagram(DomainDiagram):
    """Native format is just the standard DomainDiagram.
    
    This class exists for consistency and future extensions.
    """
    pass


# Union type for all diagram formats
DiagramFormat = Union[LightDiagram, ReadableDiagram, NativeDiagram, DomainDiagram]


def detect_diagram_format(data: Dict[str, Any]) -> type[DiagramFormat]:
    """Detect the format of a diagram from its structure."""
    if "version" in data and data["version"] == "readable":
        return ReadableDiagram
    elif "connections" in data:
        return LightDiagram
    elif "arrows" in data and "handles" in data:
        return NativeDiagram
    else:
        # Default to DomainDiagram
        return DomainDiagram


def parse_diagram(data: Dict[str, Any]) -> DiagramFormat:
    """Parse a diagram dict into the appropriate typed model."""
    format_class = detect_diagram_format(data)
    
    if format_class == LightDiagram:
        return LightDiagram(**data)
    elif format_class == ReadableDiagram:
        return ReadableDiagram(**data)
    elif format_class == NativeDiagram:
        return NativeDiagram(**data)
    else:
        return DomainDiagram(**data)


