"""Format-specific Pydantic models for type-safe diagram handling.

These models provide strong typing for different diagram formats while
maintaining compatibility with the base DomainDiagram model.
"""

from __future__ import annotations

from typing import Any, Union

from pydantic import BaseModel, Field, field_validator

from dipeo.diagram_generated import (
    DomainDiagram,
)


class LightNode(BaseModel):
    """Light format node representation."""

    type: str
    label: str | None = None
    position: dict[str, int] | None = None
    # All other properties go here as flat structure
    model_config = {"extra": "allow"}  # Allow additional fields

    @field_validator("position")
    @classmethod
    def validate_position(cls, v):
        if v and not all(k in v for k in ["x", "y"]):
            raise ValueError("Position must have x and y coordinates")
        return v


class LightConnection(BaseModel):
    """Light format connection representation."""

    from_: str = Field(alias="from")
    to: str
    label: str | None = None
    type: str | None = None
    # Additional connection properties
    model_config = {"extra": "allow"}


class LightDiagram(BaseModel):
    """Light format diagram with simplified structure.

    This format uses labels for references and has a flatter structure
    suitable for human editing in YAML.
    """

    nodes: list[LightNode]
    connections: list[LightConnection]
    persons: list[dict[str, Any]] | None = None
    api_keys: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None


class ReadableNode(BaseModel):
    """Readable format node with explicit structure."""

    id: str
    type: str
    label: str | None = None
    position: dict[str, int]
    props: dict[str, Any] = Field(default_factory=dict)

    @field_validator("position")
    @classmethod
    def validate_position(cls, v):
        if not all(k in v for k in ["x", "y"]):
            raise ValueError("Position must have x and y coordinates")
        return v


class ReadableArrow(BaseModel):
    """Readable format arrow with explicit IDs."""

    id: str
    source: str
    target: str
    source_handle: str | None = None
    target_handle: str | None = None
    label: str | None = None
    data: dict[str, Any] | None = None


class ReadableDiagram(BaseModel):
    """Readable format diagram with explicit IDs and structure.

    This format is more verbose but clearer for understanding
    the complete diagram structure.
    """

    version: str = "readable"
    nodes: list[ReadableNode]
    arrows: list[ReadableArrow]
    persons: list[dict[str, Any]] | None = None
    api_keys: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None


class NativeDiagram(DomainDiagram):
    """Native format is just the standard DomainDiagram.

    This class exists for consistency and future extensions.
    """

    pass


# Union type for all diagram formats
DiagramFormat = LightDiagram | ReadableDiagram | NativeDiagram | DomainDiagram


def detect_diagram_format(data: dict[str, Any]) -> type[DiagramFormat]:
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


def parse_diagram(data: dict[str, Any]) -> DiagramFormat:
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
