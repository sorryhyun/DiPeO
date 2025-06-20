"""Common utilities, services, and domain models."""

# Export all enums from generated models
from src.__generated__.models import (
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

# Export processors and validators
from .processors import OutputProcessor
from .validators import DiagramValidator

# Export base classes
from .base import BaseService

# Export context utilities
from .context import (
    get_api_key_service,
    get_file_service,
    get_memory_service,
    get_llm_service,
    get_diagram_service,
    get_execution_service,
    get_notion_service,
    get_app_context,
    app_context,
    lifespan,
)

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
    "BaseError",
    "ValidationError",
    "NotFoundError",
    "LLMServiceError",
    "APIKeyError",
    "ExecutionError",
    "DiagramError",
    "FileOperationError",
    "MemoryError",
    "WebSocketError",
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
    "toggle_feature",
    # Processors and validators
    "OutputProcessor",
    "DiagramValidator",
    # Base classes
    "BaseService",
    # Context utilities
    "get_api_key_service",
    "get_file_service",
    "get_memory_service",
    "get_person_service",
    "get_llm_service",
    "reset_app_context",
    # Service types
    "IAPIKeyService",
    "IFileService",
    "IMemoryService",
    "IPersonService",
    "ILLMService",
]