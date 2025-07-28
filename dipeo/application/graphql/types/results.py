"""GraphQL result types for DiPeO operations."""

import strawberry
from typing import Optional

from strawberry.scalars import JSON as JSONScalar

# Import ID scalars from domain models (if needed for type checking)

# Import Strawberry types
from .domain_types import (
    DomainDiagramType,
    ExecutionStateType,
    DomainPersonType,
    DomainApiKeyType,
    DomainNodeType
)


@strawberry.type
class DiagramOperationResult:
    success: bool
    message: Optional[str] = None
    diagram: Optional[DomainDiagramType] = None
    error: Optional[str] = None


@strawberry.type
class ExecutionResult:
    success: bool
    execution_id: Optional[str] = None
    execution: Optional[ExecutionStateType] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class FileOperationResult:
    success: bool
    message: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class PersonResult:
    success: bool
    person: Optional[DomainPersonType] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class ApiKeyResult:
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    api_key: Optional[DomainApiKeyType] = None


@strawberry.type
class DeleteResult:
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    deleted_id: Optional[str] = None


@strawberry.type
class DiagramResult:
    success: bool
    diagram: Optional[DomainDiagramType] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class NodeResult:
    success: bool
    node: Optional[DomainNodeType] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class FileUploadResult:
    success: bool
    message: Optional[str] = None
    path: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class TestApiKeyResult:
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    model_info: Optional[JSONScalar] = None


@strawberry.type
class DiagramFormatInfo:
    format: str
    name: str
    extension: str
    supports_export: bool
    supports_import: bool
    description: Optional[str] = None