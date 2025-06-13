"""Result types for GraphQL operations with error handling."""
import strawberry
from typing import Optional, List, Union

from .domain import (
    Node, Diagram, ExecutionState, Person, ApiKey
)
from .scalars import ExecutionID, DiagramID, JSONScalar

@strawberry.type
class ValidationError:
    """Validation error details."""
    field: str
    message: str
    code: Optional[str] = None

@strawberry.type
class OperationError:
    """General operation error."""
    message: str
    code: str
    details: Optional[JSONScalar] = None

@strawberry.type
class NodeResult:
    """Result of node operation."""
    success: bool
    node: Optional[Node] = None
    errors: Optional[List[ValidationError]] = None

@strawberry.type
class DiagramResult:
    """Result of diagram operation."""
    success: bool
    diagram: Optional[Diagram] = None
    errors: Optional[List[ValidationError]] = None

@strawberry.type
class ExecutionResult:
    """Result of execution operation."""
    success: bool
    execution: Optional[ExecutionState] = None
    execution_id: Optional[ExecutionID] = None
    error: Optional[OperationError] = None

@strawberry.type
class PersonResult:
    """Result of person operation."""
    success: bool
    person: Optional[Person] = None
    errors: Optional[List[ValidationError]] = None

@strawberry.type
class ApiKeyResult:
    """Result of API key operation."""
    success: bool
    api_key: Optional[ApiKey] = None
    error: Optional[OperationError] = None

@strawberry.type
class DeleteResult:
    """Result of delete operation."""
    success: bool
    deleted_id: Optional[str] = None
    error: Optional[OperationError] = None

@strawberry.type
class TestApiKeyResult:
    """Result of API key test."""
    success: bool
    message: str
    available_models: Optional[List[str]] = None
    error: Optional[str] = None

# Union types for flexible error handling
DiagramOperationResult = strawberry.union(
    "DiagramOperationResult",
    [Diagram, OperationError]
)

ExecutionOperationResult = strawberry.union(
    "ExecutionOperationResult",
    [ExecutionState, OperationError]
)