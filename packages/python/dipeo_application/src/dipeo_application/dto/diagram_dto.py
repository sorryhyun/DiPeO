"""DTOs for diagram-related operations."""

from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CreateDiagramRequest(BaseModel):
    """Request DTO for creating a diagram."""
    
    name: str = Field(..., description="Diagram name")
    description: Optional[str] = Field(None, description="Diagram description")
    nodes: list[dict[str, Any]] = Field(default_factory=list, description="Diagram nodes")
    arrows: list[dict[str, Any]] = Field(default_factory=list, description="Diagram arrows")
    persons: list[dict[str, Any]] = Field(default_factory=list, description="Diagram persons")
    apiKeys: list[dict[str, Any]] = Field(default_factory=list, description="API keys")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")


class DiagramResponse(BaseModel):
    """Response DTO for diagram operations."""
    
    id: str = Field(..., description="Diagram ID")
    name: str = Field(..., description="Diagram name")
    description: Optional[str] = Field(None, description="Diagram description")
    created: datetime = Field(..., description="Creation timestamp")
    updated: datetime = Field(..., description="Last update timestamp")
    nodes_count: int = Field(..., description="Number of nodes")
    arrows_count: int = Field(..., description="Number of arrows")
    persons_count: int = Field(..., description="Number of persons")
    
    @classmethod
    def from_domain(cls, diagram: Any) -> "DiagramResponse":
        """Create from domain model."""
        return cls(
            id=diagram.metadata.id,
            name=diagram.metadata.name or "Untitled",
            description=diagram.metadata.description,
            created=diagram.metadata.created,
            updated=diagram.metadata.updated,
            nodes_count=len(diagram.nodes),
            arrows_count=len(diagram.arrows),
            persons_count=len(diagram.persons),
        )


class UpdateDiagramRequest(BaseModel):
    """Request DTO for updating a diagram."""
    
    name: Optional[str] = Field(None, description="New diagram name")
    description: Optional[str] = Field(None, description="New diagram description")
    nodes: Optional[list[dict[str, Any]]] = Field(None, description="Updated nodes")
    arrows: Optional[list[dict[str, Any]]] = Field(None, description="Updated arrows")
    persons: Optional[list[dict[str, Any]]] = Field(None, description="Updated persons")
    metadata: Optional[dict[str, Any]] = Field(None, description="Updated metadata")


class ListDiagramsRequest(BaseModel):
    """Request DTO for listing diagrams."""
    
    search: Optional[str] = Field(None, description="Search term")
    tags: Optional[list[str]] = Field(None, description="Filter by tags")
    limit: int = Field(100, ge=1, le=1000, description="Results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")
    sort_by: str = Field("updated", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


class ListDiagramsResponse(BaseModel):
    """Response DTO for listing diagrams."""
    
    diagrams: list[DiagramResponse] = Field(..., description="List of diagrams")
    total: int = Field(..., description="Total number of diagrams")
    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Current offset")