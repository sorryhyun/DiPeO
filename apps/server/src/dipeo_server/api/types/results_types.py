"""GraphQL result types for API operations."""

from typing import Optional

import strawberry

from .domain_types import (
    DomainDiagramType,
    ExecutionState,
)
from ..models.result_models import (
    ApiKeyResultModel,
    ArrowResultModel,
    DeleteResultModel,
    DiagramResultModel,
    ExecutionResultModel,
    FileUploadResultModel,
    HandleResultModel,
    NodeResultModel,
    OperationErrorModel,
    PersonResultModel,
    TestApiKeyResultModel,
)


@strawberry.type
class ValidationError:
    """Validation error info."""

    field: str
    message: str
    code: Optional[str] = None


@strawberry.type
class DiagramFormatInfo:
    """Diagram format details."""

    id: str
    name: str
    description: str
    extension: str
    supports_import: bool
    supports_export: bool


@strawberry.experimental.pydantic.type(
    model=OperationErrorModel, all_fields=True, description="General operation error"
)
class OperationError:
    pass


@strawberry.experimental.pydantic.type(
    model=DeleteResultModel, all_fields=True, description="Result of delete operation"
)
class DeleteResult:
    pass


@strawberry.experimental.pydantic.type(
    model=NodeResultModel, all_fields=True, description="Result of node operation"
)
class NodeResult:
    pass


@strawberry.experimental.pydantic.type(
    model=HandleResultModel, all_fields=True, description="Result of handle operation"
)
class HandleResult:
    pass


@strawberry.experimental.pydantic.type(
    model=ArrowResultModel, all_fields=True, description="Result of arrow operation"
)
class ArrowResult:
    pass


@strawberry.experimental.pydantic.type(
    model=PersonResultModel, all_fields=True, description="Result of person operation"
)
class PersonResult:
    pass


@strawberry.experimental.pydantic.type(
    model=ApiKeyResultModel, all_fields=True, description="Result of API key operation"
)
class ApiKeyResult:
    pass


@strawberry.experimental.pydantic.type(
    model=DiagramResultModel, all_fields=True, description="Result of diagram operation"
)
class DiagramResult:
    pass


@strawberry.experimental.pydantic.type(
    model=ExecutionResultModel,
    all_fields=True,
    description="Result of execution operation",
)
class ExecutionResult:
    pass


@strawberry.experimental.pydantic.type(
    model=TestApiKeyResultModel, all_fields=True, description="Result of API key test"
)
class TestApiKeyResult:
    pass


@strawberry.experimental.pydantic.type(
    model=FileUploadResultModel,
    all_fields=True,
    description="Result of file upload operation",
)
class FileUploadResult:
    pass


DiagramOperationResult = strawberry.union(
    "DiagramOperationResult", [DomainDiagramType, OperationError]
)

ExecutionOperationResult = strawberry.union(
    "ExecutionOperationResult", [ExecutionState, OperationError]
)
