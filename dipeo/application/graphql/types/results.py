"""GraphQL result types for DiPeO operations."""

import strawberry
from strawberry.scalars import JSON

# Import ID scalars from domain models (if needed for type checking)
# Import Strawberry types from generated code
from dipeo.diagram_generated.graphql.domain_types import (
    DomainApiKeyType,
    DomainDiagramType,
    DomainNodeType,
    DomainPersonType,
    ExecutionStateType,
)


@strawberry.type
class DiagramOperationResult:
    success: bool
    message: str | None = None
    diagram: DomainDiagramType | None = None
    error: str | None = None


@strawberry.type
class ExecutionResult:
    success: bool
    execution_id: str | None = None
    execution: ExecutionStateType | None = None
    message: str | None = None
    error: str | None = None


@strawberry.type
class FileOperationResult:
    success: bool
    message: str | None = None
    content: str | None = None
    error: str | None = None


@strawberry.type
class PersonResult:
    success: bool
    person: DomainPersonType | None = None
    message: str | None = None
    error: str | None = None


@strawberry.type
class ApiKeyResult:
    success: bool
    message: str | None = None
    error: str | None = None
    api_key: DomainApiKeyType | None = None


@strawberry.type
class DeleteResult:
    success: bool
    message: str | None = None
    error: str | None = None
    deleted_id: str | None = None


@strawberry.type
class DiagramResult:
    success: bool
    diagram: DomainDiagramType | None = None
    message: str | None = None
    error: str | None = None


@strawberry.type
class NodeResult:
    success: bool
    node: DomainNodeType | None = None
    message: str | None = None
    error: str | None = None


@strawberry.type
class FileUploadResult:
    success: bool
    message: str | None = None
    path: str | None = None
    size_bytes: int | None = None
    content_type: str | None = None
    error: str | None = None


@strawberry.type
class TestApiKeyResult:
    success: bool
    message: str | None = None
    error: str | None = None
    model_info: JSON | None = None


@strawberry.type
class DiagramFormatInfo:
    format: str
    name: str
    extension: str
    supports_export: bool
    supports_import: bool
    description: str | None = None


@strawberry.type
class CliSessionResult:
    success: bool
    message: str | None = None
    error: str | None = None
