"""
DO NOT EDIT - Generated unified result types for GraphQL operations

This file provides type-safe result types for all GraphQL operations,
following the Envelope pattern from the domain layer.
Generated at: 2025-09-17T19:31:22.449458
"""

import strawberry
from typing import Optional, Any
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


# Base result fields mixin for consistent structure
class BaseResultMixin:
    """Common fields for all result types"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None  # Raw envelope for advanced use cases

    @classmethod
    def from_envelope(cls, envelope: Envelope, data: Optional[Any] = None):
        """Create result from domain Envelope"""
        instance = cls(
            success=not envelope.has_error(),
            message=envelope.meta.get("message"),
            error=envelope.error,
            error_type=envelope.meta.get("error_type"),
            envelope=envelope.meta
        )
        if data is not None and hasattr(instance, 'data'):
            instance.data = data
        return instance

    @classmethod
    def success_result(cls, data: Any, message: Optional[str] = None):
        """Create a successful result"""
        instance = cls(
            success=True,
            message=message
        )
        if hasattr(instance, 'data'):
            instance.data = data
        # Set entity-specific field if it exists
        if hasattr(instance, 'diagram') and hasattr(data, '__class__') and 'Diagram' in data.__class__.__name__:
            instance.diagram = data
        elif hasattr(instance, 'node') and hasattr(data, '__class__') and 'Node' in data.__class__.__name__:
            instance.node = data
        elif hasattr(instance, 'person') and hasattr(data, '__class__') and 'Person' in data.__class__.__name__:
            instance.person = data
        elif hasattr(instance, 'api_key') and hasattr(data, '__class__') and 'ApiKey' in data.__class__.__name__:
            instance.api_key = data
        elif hasattr(instance, 'execution') and hasattr(data, '__class__') and 'Execution' in data.__class__.__name__:
            instance.execution = data
        return instance

    @classmethod
    def error_result(cls, error: str, error_type: str = "OperationError", message: Optional[str] = None):
        """Create an error result"""
        return cls(
            success=False,
            error=error,
            error_type=error_type,
            message=message or error
        )


# Specific result types for each entity/operation type

@strawberry.type
class DiagramResult(BaseResultMixin):
    """Result type for diagram operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[DomainDiagramType] = None
    # Deprecated field for backward compatibility
    diagram: Optional[DomainDiagramType] = strawberry.field(
        default=None,
        deprecation_reason="Use 'data' field instead"
    )

    def __post_init__(self):
        # Auto-populate deprecated field
        if self.data and not self.diagram:
            self.diagram = self.data


@strawberry.type
class DiagramListResult(BaseResultMixin):
    """Result type for diagram list operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[list[DomainDiagramType]] = None
    total_count: Optional[int] = None
    has_more: Optional[bool] = None


@strawberry.type
class NodeResult(BaseResultMixin):
    """Result type for node operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[DomainNodeType] = None
    # Deprecated field for backward compatibility
    node: Optional[DomainNodeType] = strawberry.field(
        default=None,
        deprecation_reason="Use 'data' field instead"
    )

    def __post_init__(self):
        # Auto-populate deprecated field
        if self.data and not self.node:
            self.node = self.data


@strawberry.type
class NodeListResult(BaseResultMixin):
    """Result type for node list operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[list[DomainNodeType]] = None
    total_count: Optional[int] = None


@strawberry.type
class ExecutionResult(BaseResultMixin):
    """Result type for execution operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[ExecutionStateType] = None
    # Deprecated field for backward compatibility
    execution: Optional[ExecutionStateType] = strawberry.field(
        default=None,
        deprecation_reason="Use 'data' field instead"
    )

    def __post_init__(self):
        # Auto-populate deprecated field
        if self.data and not self.execution:
            self.execution = self.data


@strawberry.type
class ExecutionListResult(BaseResultMixin):
    """Result type for execution list operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[list[ExecutionStateType]] = None
    total_count: Optional[int] = None
    active_count: Optional[int] = None


@strawberry.type
class PersonResult(BaseResultMixin):
    """Result type for person operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[DomainPersonType] = None
    # Deprecated field for backward compatibility
    person: Optional[DomainPersonType] = strawberry.field(
        default=None,
        deprecation_reason="Use 'data' field instead"
    )

    def __post_init__(self):
        # Auto-populate deprecated field
        if self.data and not self.person:
            self.person = self.data


@strawberry.type
class PersonListResult(BaseResultMixin):
    """Result type for person list operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[list[DomainPersonType]] = None
    total_count: Optional[int] = None


@strawberry.type
class ApiKeyResult(BaseResultMixin):
    """Result type for API key operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[DomainApiKeyType] = None
    # Deprecated field for backward compatibility
    api_key: Optional[DomainApiKeyType] = strawberry.field(
        default=None,
        deprecation_reason="Use 'data' field instead"
    )

    def __post_init__(self):
        # Auto-populate deprecated field
        if self.data and not self.api_key:
            self.api_key = self.data


@strawberry.type
class ApiKeyListResult(BaseResultMixin):
    """Result type for API key list operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[list[DomainApiKeyType]] = None
    total_count: Optional[int] = None


@strawberry.type
class ConversationResult(BaseResultMixin):
    """Result type for conversation operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[JSON] = None


@strawberry.type
class ConversationListResult(BaseResultMixin):
    """Result type for conversation list operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[list[JSON]] = None
    total_count: Optional[int] = None


@strawberry.type
class FileOperationResult(BaseResultMixin):
    """Result type for file operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[JSON] = None
    path: Optional[str] = None
    content: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None


@strawberry.type
class DeleteResult(BaseResultMixin):
    """Result type for delete operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[JSON] = None  # Delete operations typically don't return data
    deleted_id: Optional[str] = None
    deleted_count: Optional[int] = None


@strawberry.type
class TestResult(BaseResultMixin):
    """Result type for test operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[JSON] = None
    test_name: Optional[str] = None
    duration_ms: Optional[float] = None
    model_info: Optional[JSON] = None


@strawberry.type
class FormatConversionResult(BaseResultMixin):
    """Result type for format conversion operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[str] = None
    format: Optional[str] = None
    original_format: Optional[str] = None


@strawberry.type
class ValidationResult(BaseResultMixin):
    """Result type for validation operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[bool] = None
    warnings: Optional[list[str]] = None
    errors: Optional[list[str]] = None
    is_valid: Optional[bool] = None


@strawberry.type
class CliSessionResult(BaseResultMixin):
    """Result type for CLI session operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[JSON] = None
    session_id: Optional[str] = None
    execution_id: Optional[str] = None


@strawberry.type
class InteractiveResponseResult(BaseResultMixin):
    """Result type for interactive response operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[JSON] = None
    node_id: Optional[str] = None
    execution_id: Optional[str] = None
    response_data: Optional[JSON] = None


@strawberry.type
class BatchOperationResult(BaseResultMixin):
    """Result type for batch operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    envelope: Optional[JSON] = None
    data: Optional[list[JSON]] = None
    succeeded_count: Optional[int] = None
    failed_count: Optional[int] = None
    partial_failures: Optional[list[JSON]] = None


# Helper functions for creating results from different sources

def create_success_result(data: Any, result_type: type, message: Optional[str] = None):
    """Create a successful result with type checking"""
    return result_type.success_result(data=data, message=message)


def create_error_result(error: str, result_type: type, error_type: str = "OperationError"):
    """Create an error result with type checking"""
    return result_type.error_result(error=error, error_type=error_type)


def create_result_from_envelope(envelope: Envelope, result_type: type, data: Optional[Any] = None):
    """Create a result from a domain Envelope"""
    return result_type.from_envelope(envelope=envelope, data=data)


# Export all result types
__all__ = [
    'BaseResultMixin',
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
