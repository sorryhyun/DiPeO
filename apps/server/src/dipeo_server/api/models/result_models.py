"""Pydantic models for GraphQL result types."""

from typing import Any, Dict, List, Optional

from dipeo_domain import (
    DomainApiKey,
    DomainArrow,
    DomainDiagram,
    DomainHandle,
    DomainNode,
    DomainPerson,
    ExecutionState,
)
from pydantic import BaseModel, Field


class DeleteResultModel(BaseModel):
    """Result of a delete operation."""

    success: bool
    message: Optional[str] = None
    deleted_id: Optional[str] = Field(None, alias="deletedId")
    error: Optional[str] = None


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
    execution_id: Optional[str] = Field(None, alias="executionId")
    message: Optional[str] = None
    error: Optional[str] = None


class TestApiKeyResultModel(BaseModel):
    """Result of testing an API key."""

    success: bool
    valid: Optional[bool] = None
    available_models: Optional[List[str]] = Field(None, alias="availableModels")
    message: Optional[str] = None
    error: Optional[str] = None


class FileUploadResultModel(BaseModel):
    """Result of a file upload operation."""

    success: bool
    path: Optional[str] = None
    size_bytes: Optional[int] = Field(None, alias="sizeBytes")
    content_type: Optional[str] = Field(None, alias="contentType")
    message: Optional[str] = None
    error: Optional[str] = None


class OperationErrorModel(BaseModel):
    """Error details for failed operations."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
