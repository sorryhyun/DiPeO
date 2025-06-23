"""Pydantic models for diagram converter and storage services."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BackendDiagram(BaseModel):
    """Backend representation of a diagram (dict of dicts).

    This is a simple wrapper around the dict format used for storage and execution.
    Fields are untyped dicts to avoid unnecessary conversions.
    """
    nodes: Dict[str, Any] = Field(default_factory=dict)
    arrows: Dict[str, Any] = Field(default_factory=dict)
    persons: Dict[str, Any] = Field(default_factory=dict)
    handles: Dict[str, Any] = Field(default_factory=dict)
    api_keys: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"  # Allow additional fields like _execution_hints


class ExecutionHint(BaseModel):
    """Execution hint for a node dependency."""
    source: str
    variable: str = "flow"


class ExecutionHints(BaseModel):
    """Execution hints for the diagram."""
    start_nodes: List[str] = Field(default_factory=list)
    node_dependencies: Dict[str, List[ExecutionHint]] = Field(default_factory=dict)
    person_nodes: Dict[str, str] = Field(default_factory=dict)


class ReadableFlow(BaseModel):
    """Readable YAML representation."""
    flow: List[str]
    prompts: Optional[Dict[str, str]] = None
    agents: Optional[Dict[str, Dict[str, Any]]] = None


class ExecutionPreparation(BaseModel):
    """Result of preparing a diagram for execution."""
    diagram_id: str
    backend_format: BackendDiagram
    api_keys: Dict[str, str]
    execution_hints: ExecutionHints
    domain_model: Optional[Any] = None  # DomainDiagram


class ExecutionReadyDiagram(BaseModel):
    """Diagram ready for execution with all necessary data."""
    diagram_id: str
    backend_format: Dict[str, Any]  # Execution format with hints
    api_keys: Dict[str, str]
    execution_hints: ExecutionHints
    domain_model: Optional[Any] = None  # DomainDiagram


class FileInfo(BaseModel):
    """Information about a diagram file."""
    id: str
    name: str
    path: str
    format: str
    extension: str
    modified: str
    size: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return self.model_dump()
