"""Common utilities, services, and domain models."""

# Export all enums from generated models
from dipeo_domain import (
    ContentType,
    DataType,
    DBBlockSubType,
    DiagramFormat,
    ExecutionStatus,
    ForgettingMode,
    HandleDirection,
    LLMService,
    NodeType,
)

from ..domains.diagram.services import DiagramService
from ..domains.execution.services.execution_service import ExecutionService
from ..domains.integrations.notion import NotionService
from ..domains.llm.services import LLMService

# Export base classes
from .base import BaseService

# Export all constants
from .constants import (
    API_BASE_PATH,
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_EXECUTION_TIMEOUT,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MEMORY_LIMIT,
    DEFAULT_SERVICE,
    DEFAULT_TEMPERATURE,
    SERVICE_ALIASES,
    SUPPORTED_CODE_EXTENSIONS,
    SUPPORTED_DIAGRAM_EXTENSIONS,
    SUPPORTED_DOC_EXTENSIONS,
    VALID_LLM_SERVICES,
)

# Export exceptions
from .exceptions import (
    AgentDiagramException,
    APIKeyError,
    APIKeyNotFoundError,
    ConditionEvaluationError,
    ConfigurationError,
    DatabaseError,
    DependencyError,
    DiagramExecutionError,
    FileOperationError,
    LLMServiceError,
    MaxIterationsError,
    NodeExecutionError,
    PersonJobExecutionError,
    ValidationError,
)

# Export processors
from .processors import OutputProcessor

# Export context utilities - imported lazily to avoid circular imports
# Use these functions directly from src.common.context when needed
# Export service types
from .service_types import (
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)

# Export services
from .services import APIKeyService, FileService

# Export all type aliases and base models
from .types import (
    ApiKeyID,
    ArrowID,
    DiagramID,
    ExecutionID,
    HandleID,
    NodeID,
    PersonID,
    TimestampedModel,
    TokenUsage,
    Vec2,
)

# Export utils
from .utils import (
    ErrorHandler,
    FeatureFlag,
    FeatureFlagManager,
    ResponseFormatter,
    configure_features,
    disable_feature,
    enable_feature,
    get_feature_flags,
    get_feature_status,
    handle_api_errors,
    handle_internal_errors,
    handle_service_exceptions,
    is_feature_enabled,
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
    "LLMService",
    "DiagramService",
    "ExecutionService",
    "NotionService",
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
