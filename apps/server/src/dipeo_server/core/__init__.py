"""Common utilities, services, and domain models."""

# Export all enums from generated models
from dipeo_domain import (
    NodeType,
    HandleDirection,
    DataType,
    LLMService,
    ForgettingMode,
    DiagramFormat,
    ExecutionStatus,
    DBBlockSubType,
    ContentType,
)

# Export all type aliases and base models
from .types import (
    NodeID,
    ArrowID,
    HandleID,
    PersonID,
    ApiKeyID,
    DiagramID,
    ExecutionID,
    Vec2,
    TokenUsage,
    TimestampedModel,
)

# Export all constants
from .constants import (
    API_BASE_PATH,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    SUPPORTED_DOC_EXTENSIONS,
    SUPPORTED_CODE_EXTENSIONS,
    SUPPORTED_DIAGRAM_EXTENSIONS,
    SERVICE_ALIASES,
    VALID_LLM_SERVICES,
    DEFAULT_SERVICE,
    DEFAULT_EXECUTION_TIMEOUT,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MEMORY_LIMIT,
    DEFAULT_CONTEXT_WINDOW,
)

# Export exceptions
from .exceptions import (
    AgentDiagramException,
    ValidationError,
    APIKeyError,
    APIKeyNotFoundError,
    LLMServiceError,
    DiagramExecutionError,
    NodeExecutionError,
    DependencyError,
    MaxIterationsError,
    ConditionEvaluationError,
    PersonJobExecutionError,
    FileOperationError,
    DatabaseError,
    ConfigurationError,
)

# Export services
from .services import APIKeyService, FileService

# Export utils
from .utils import (
    ResponseFormatter,
    ErrorHandler,
    FeatureFlagManager,
    FeatureFlag,
    handle_service_exceptions,
    handle_api_errors,
    handle_internal_errors,
    get_feature_status,
    enable_feature,
    disable_feature,
    is_feature_enabled,
    configure_features,
    get_feature_flags,
)

# Export processors
from .processors import OutputProcessor

# Export base classes
from .base import BaseService

# Export context utilities - imported lazily to avoid circular imports
# Use these functions directly from src.common.context when needed

# Export service types
from .service_types import (
    SupportsAPIKey,
    SupportsFile,
    SupportsMemory,
    SupportsLLM,
    SupportsDiagram,
    SupportsExecution,
    SupportsNotion,
)

__all__ = [
    # Enums
    "NodeType",
    "HandleDirection",
    "DataType",
    "LLMService",
    "ForgettingMode",
    "DiagramFormat",
    "ExecutionStatus",
    "DBBlockSubType",
    "ContentType",
    # Types
    "NodeID",
    "ArrowID",
    "HandleID",
    "PersonID",
    "ApiKeyID",
    "DiagramID",
    "ExecutionID",
    "Vec2",
    "TokenUsage",
    "TimestampedModel",
    # Constants
    "API_BASE_PATH",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_TEMPERATURE",
    "SUPPORTED_DOC_EXTENSIONS",
    "SUPPORTED_CODE_EXTENSIONS",
    "SUPPORTED_DIAGRAM_EXTENSIONS",
    "SERVICE_ALIASES",
    "VALID_LLM_SERVICES",
    "DEFAULT_SERVICE",
    "DEFAULT_EXECUTION_TIMEOUT",
    "DEFAULT_MAX_ITERATIONS",
    "DEFAULT_MEMORY_LIMIT",
    "DEFAULT_CONTEXT_WINDOW",
    # Exceptions
    "AgentDiagramException",
    "ValidationError",
    "LLMServiceError",
    "APIKeyError",
    "APIKeyNotFoundError",
    "DiagramExecutionError",
    "NodeExecutionError",
    "DependencyError",
    "MaxIterationsError",
    "ConditionEvaluationError",
    "PersonJobExecutionError",
    "FileOperationError",
    "DatabaseError",
    "ConfigurationError",
    # Services
    "APIKeyService",
    "FileService",
    # Utils
    "ResponseFormatter",
    "ErrorHandler",
    "FeatureFlagManager",
    "FeatureFlag",
    "handle_service_exceptions",
    "handle_api_errors",
    "handle_internal_errors",
    "get_feature_status",
    "enable_feature",
    "disable_feature",
    "is_feature_enabled",
    "configure_features",
    "get_feature_flags",
    # Processors
    "OutputProcessor",
    # Base classes
    "BaseService",
    # Service types
    "SupportsAPIKey",
    "SupportsFile",
    "SupportsMemory",
    "SupportsLLM",
    "SupportsDiagram",
    "SupportsExecution",
    "SupportsNotion",
]