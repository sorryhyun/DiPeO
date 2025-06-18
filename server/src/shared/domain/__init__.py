"""
Shared domain models, enums, and types.
This module contains the core domain vocabulary used across all domains.
"""

# Import enums from generated models
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
    ContextCleaningRule,
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
    SERVICE_TO_PROVIDER_MAP,
    PROVIDER_TO_ENUM_MAP,
    DEFAULT_SERVICE,
    DEFAULT_EXECUTION_TIMEOUT,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MEMORY_LIMIT,
    DEFAULT_CONTEXT_WINDOW,
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
    "ContextCleaningRule",
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
    "SERVICE_TO_PROVIDER_MAP",
    "PROVIDER_TO_ENUM_MAP",
    "DEFAULT_SERVICE",
    "DEFAULT_EXECUTION_TIMEOUT",
    "DEFAULT_MAX_ITERATIONS",
    "DEFAULT_MEMORY_LIMIT",
    "DEFAULT_CONTEXT_WINDOW",
]