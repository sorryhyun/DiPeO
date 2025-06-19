"""Result types for GraphQL operations with error handling."""
import strawberry
from typing import Optional, List, Union

from .domain import (
    Node, DomainDiagramType, ExecutionState, Person, ApiKey, Handle
)
from .scalars import ExecutionID, DiagramID, JSONScalar
from ..models.result_models import (
    DeleteResultModel,
    NodeResultModel,
    HandleResultModel,
    ArrowResultModel,
    PersonResultModel,
    ApiKeyResultModel,
    DiagramResultModel,
    ExecutionResultModel,
    TestApiKeyResultModel,
    FileUploadResultModel,
    OperationErrorModel
)

# Validation error stays as pure Strawberry type (simple structure)
@strawberry.type
class ValidationError:
    """Validation error details."""
    field: str
    message: str
    code: Optional[str] = None

# Convert Pydantic models to Strawberry types
OperationError = strawberry.experimental.pydantic.type(
    model=OperationErrorModel,
    all_fields=True,
    description="General operation error"
)

DeleteResult = strawberry.experimental.pydantic.type(
    model=DeleteResultModel,
    all_fields=True,
    description="Result of delete operation"
)

NodeResult = strawberry.experimental.pydantic.type(
    model=NodeResultModel,
    all_fields=True,
    description="Result of node operation"
)

HandleResult = strawberry.experimental.pydantic.type(
    model=HandleResultModel,
    all_fields=True,
    description="Result of handle operation"
)

ArrowResult = strawberry.experimental.pydantic.type(
    model=ArrowResultModel,
    all_fields=True,
    description="Result of arrow operation"
)

PersonResult = strawberry.experimental.pydantic.type(
    model=PersonResultModel,
    all_fields=True,
    description="Result of person operation"
)

ApiKeyResult = strawberry.experimental.pydantic.type(
    model=ApiKeyResultModel,
    all_fields=True,
    description="Result of API key operation"
)

DiagramResult = strawberry.experimental.pydantic.type(
    model=DiagramResultModel,
    all_fields=True,
    description="Result of diagram operation"
)

ExecutionResult = strawberry.experimental.pydantic.type(
    model=ExecutionResultModel,
    all_fields=True,
    description="Result of execution operation"
)

TestApiKeyResult = strawberry.experimental.pydantic.type(
    model=TestApiKeyResultModel,
    all_fields=True,
    description="Result of API key test"
)

FileUploadResult = strawberry.experimental.pydantic.type(
    model=FileUploadResultModel,
    all_fields=True,
    description="Result of file upload operation"
)

# Union types for flexible error handling
DiagramOperationResult = strawberry.union(
    "DiagramOperationResult",
    [DomainDiagramType, OperationError]
)

ExecutionOperationResult = strawberry.union(
    "ExecutionOperationResult",
    [ExecutionState, OperationError]
)