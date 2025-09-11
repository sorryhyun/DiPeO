"""
DO NOT EDIT - Generated unified result types for GraphQL operations

This file provides type-safe result types for all GraphQL operations,
following the Envelope pattern from the domain layer.
"""

import strawberry
from typing import TypeVar, Generic, Optional, Any
from strawberry.scalars import JSON
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

# Import all domain types that results may reference
from dipeo.diagram_generated.graphql.domain_types import (
    DomainApiKeyType,
    DomainDiagramType,
    DomainNodeType,
    DomainPersonType,
    ExecutionStateType,
    DomainHandleType,
    DomainArrowType,
    NodeStateType,
)

# Generic type variable for result data
T = TypeVar('T')


@strawberry.type
class OperationResult(Generic[T]):
    """
    Generic result wrapper following the Envelope pattern.
    All GraphQL operations return this unified structure.
    """
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    data: Optional[T] = None
    envelope: Optional[JSON] = None  # Raw envelope for advanced use cases

    @classmethod
    def from_envelope(cls, envelope: Envelope, data: Optional[T] = None) -> 'OperationResult[T]':
        """Create result from domain Envelope"""
        return cls(
            success=not envelope.has_error(),
            message=envelope.meta.get("message"),
            error=envelope.error,
            error_type=envelope.meta.get("error_type"),
            data=data if data is not None else envelope.body,
            envelope=envelope.meta
        )

    @classmethod
    def success_result(cls, data: T, message: Optional[str] = None) -> 'OperationResult[T]':
        """Create a successful result"""
        return cls(
            success=True,
            data=data,
            message=message
        )

    @classmethod
    def error_result(cls, error: str, error_type: str = "OperationError", message: Optional[str] = None) -> 'OperationResult[T]':
        """Create an error result"""
        return cls(
            success=False,
            error=error,
            error_type=error_type,
            message=message or error
        )


# Specific result types for each entity/operation type

@strawberry.type
class DiagramResult(OperationResult[DomainDiagramType]):
    """Result type for diagram operations"""
    diagram: Optional[DomainDiagramType] = None
    
    @classmethod
    def success_result(cls, data: DomainDiagramType, message: Optional[str] = None) -> 'DiagramResult':
        """Create a successful result with diagram field populated"""
        result = super(DiagramResult, cls).success_result(data, message)
        result.diagram = data
        return result


@strawberry.type
class DiagramListResult(OperationResult[list[DomainDiagramType]]):
    """Result type for diagram list operations"""
    total_count: Optional[int] = None
    has_more: Optional[bool] = None


@strawberry.type
class NodeResult(OperationResult[DomainNodeType]):
    """Result type for node operations"""
    node: Optional[DomainNodeType] = None
    
    @classmethod
    def success_result(cls, data: DomainNodeType, message: Optional[str] = None) -> 'NodeResult':
        """Create a successful result with node field populated"""
        result = super(NodeResult, cls).success_result(data, message)
        result.node = data
        return result


@strawberry.type
class NodeListResult(OperationResult[list[DomainNodeType]]):
    """Result type for node list operations"""
    total_count: Optional[int] = None


@strawberry.type
class ExecutionResult(OperationResult[ExecutionStateType]):
    """Result type for execution operations"""
    execution: Optional[ExecutionStateType] = None
    
    @classmethod
    def success_result(cls, data: ExecutionStateType, message: Optional[str] = None) -> 'ExecutionResult':
        """Create a successful result with execution field populated"""
        result = super(ExecutionResult, cls).success_result(data, message)
        result.execution = data
        return result


@strawberry.type
class ExecutionListResult(OperationResult[list[ExecutionStateType]]):
    """Result type for execution list operations"""
    total_count: Optional[int] = None
    active_count: Optional[int] = None


@strawberry.type
class PersonResult(OperationResult[DomainPersonType]):
    """Result type for person operations"""
    person: Optional[DomainPersonType] = None
    
    @classmethod
    def success_result(cls, data: DomainPersonType, message: Optional[str] = None) -> 'PersonResult':
        """Create a successful result with person field populated"""
        result = super(PersonResult, cls).success_result(data, message)
        result.person = data
        return result


@strawberry.type
class PersonListResult(OperationResult[list[DomainPersonType]]):
    """Result type for person list operations"""
    total_count: Optional[int] = None


@strawberry.type
class ApiKeyResult(OperationResult[DomainApiKeyType]):
    """Result type for API key operations"""
    api_key: Optional[DomainApiKeyType] = None
    
    @classmethod
    def success_result(cls, data: DomainApiKeyType, message: Optional[str] = None) -> 'ApiKeyResult':
        """Create a successful result with api_key field populated"""
        result = super(ApiKeyResult, cls).success_result(data, message)
        result.api_key = data
        return result


@strawberry.type
class ApiKeyListResult(OperationResult[list[DomainApiKeyType]]):
    """Result type for API key list operations"""
    total_count: Optional[int] = None


@strawberry.type
class ConversationResult(OperationResult[JSON]):
    """Result type for conversation operations"""
    pass


@strawberry.type
class ConversationListResult(OperationResult[list[JSON]]):
    """Result type for conversation list operations"""
    total_count: Optional[int] = None


@strawberry.type
class FileOperationResult(OperationResult[JSON]):
    """Result type for file operations"""
    path: Optional[str] = None
    content: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None


@strawberry.type
class DeleteResult(OperationResult[None]):
    """Result type for delete operations"""
    deleted_id: Optional[str] = None
    deleted_count: Optional[int] = None


@strawberry.type
class TestResult(OperationResult[JSON]):
    """Result type for test operations"""
    test_name: Optional[str] = None
    duration_ms: Optional[float] = None
    model_info: Optional[JSON] = None


@strawberry.type
class FormatConversionResult(OperationResult[str]):
    """Result type for format conversion operations"""
    format: Optional[str] = None
    original_format: Optional[str] = None


@strawberry.type
class ValidationResult(OperationResult[bool]):
    """Result type for validation operations"""
    warnings: Optional[list[str]] = None
    errors: Optional[list[str]] = None
    is_valid: Optional[bool] = None


@strawberry.type
class CliSessionResult(OperationResult[JSON]):
    """Result type for CLI session operations"""
    session_id: Optional[str] = None
    execution_id: Optional[str] = None


@strawberry.type
class InteractiveResponseResult(OperationResult[JSON]):
    """Result type for interactive response operations"""
    node_id: Optional[str] = None
    execution_id: Optional[str] = None
    response_data: Optional[JSON] = None


@strawberry.type
class BatchOperationResult(OperationResult[list[JSON]]):
    """Result type for batch operations"""
    succeeded_count: Optional[int] = None
    failed_count: Optional[int] = None
    partial_failures: Optional[list[JSON]] = None


# Helper functions for creating results from different sources

def create_success_result(data: Any, result_type: type[OperationResult], message: Optional[str] = None) -> OperationResult:
    """Create a successful result with type checking"""
    return result_type.success_result(data=data, message=message)


def create_error_result(error: str, result_type: type[OperationResult], error_type: str = "OperationError") -> OperationResult:
    """Create an error result with type checking"""
    return result_type.error_result(error=error, error_type=error_type)


def create_result_from_envelope(envelope: Envelope, result_type: type[OperationResult], data: Optional[Any] = None) -> OperationResult:
    """Create a result from a domain Envelope"""
    return result_type.from_envelope(envelope=envelope, data=data)


# Export all result types
__all__ = [
    'OperationResult',
    'DiagramResult',
    'DiagramListResult',
    'NodeResult',
    'NodeListResult',
    'ExecutionResult',
    'ExecutionListResult',
    'PersonResult',
    'PersonListResult',
    'ApiKeyResult',
    'ApiKeyListResult',
    'ConversationResult',
    'ConversationListResult',
    'FileOperationResult',
    'DeleteResult',
    'TestResult',
    'FormatConversionResult',
    'ValidationResult',
    'CliSessionResult',
    'InteractiveResponseResult',
    'BatchOperationResult',
    'create_success_result',
    'create_error_result',
    'create_result_from_envelope',
]
