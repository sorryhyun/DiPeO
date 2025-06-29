"""Pydantic models for diagram converter and storage services."""

from typing import Any

from pydantic import BaseModel, Field


class BackendDiagram(BaseModel):
    """Backend representation of a diagram (dict of dicts).

    This is a simple wrapper around the dict format used for storage and execution.
    Fields are untyped dicts to avoid unnecessary conversions.
    """

    nodes: dict[str, Any] = Field(default_factory=dict)
    arrows: dict[str, Any] = Field(default_factory=dict)
    persons: dict[str, Any] = Field(default_factory=dict)
    handles: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] | None = None

    class Config:
        extra = "allow"  # Allow additional fields like _execution_hints


class ReadableFlow(BaseModel):
    """Readable YAML representation."""

    flow: list[str]
    prompts: dict[str, str] | None = None
    agents: dict[str, dict[str, Any]] | None = None


class FileInfo(BaseModel):
    """Information about a diagram file."""

    id: str
    name: str
    path: str
    format: str
    extension: str
    modified: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return self.model_dump()