"""Pydantic models for GraphQL result types."""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from src.__generated__.models import (
    DomainNode, DomainHandle, DomainArrow, DomainPerson,
    DomainApiKey, DomainDiagram, DiagramMetadata,
    ExecutionState, DiagramID
)


class DeleteResultModel(BaseModel):
    """Result of a delete operation."""
    success: bool
    message: Optional[str] = None


class NodeResultModel(BaseModel):
    """Result of a node operation."""
    success: bool
    node: Optional[DomainNode] = None
    message: Optional[str] = None
    error: Optional[str] = None


class HandleResultModel(BaseModel):
    """Result of a handle operation."""
    success: bool
    handle: Optional[DomainHandle] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ArrowResultModel(BaseModel):
    """Result of an arrow operation."""
    success: bool
    arrow: Optional[DomainArrow] = None
    message: Optional[str] = None
    error: Optional[str] = None


class PersonResultModel(BaseModel):
    """Result of a person operation."""
    success: bool
    person: Optional[DomainPerson] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ApiKeyResultModel(BaseModel):
    """Result of an API key operation."""
    success: bool
    api_key: Optional[DomainApiKey] = Field(None, alias="apiKey")
    message: Optional[str] = None
    error: Optional[str] = None


class DiagramResultModel(BaseModel):
    """Result of a diagram operation."""
    success: bool
    diagram: Optional[DomainDiagram] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ExecutionResultModel(BaseModel):
    """Result of an execution operation."""
    success: bool
    execution: Optional[ExecutionState] = None
    message: Optional[str] = None
    error: Optional[str] = None


class TestApiKeyResultModel(BaseModel):
    """Result of testing an API key."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class FileUploadResultModel(BaseModel):
    """Result of a file upload operation."""
    success: bool
    diagram_id: Optional[DiagramID] = Field(None, alias="diagramId")
    message: Optional[str] = None
    errors: Optional[List[str]] = None


class OperationErrorModel(BaseModel):
    """Error details for failed operations."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None