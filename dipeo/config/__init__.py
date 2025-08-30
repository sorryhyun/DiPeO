"""Unified configuration module for DiPeO.

This module provides centralized configuration management using Pydantic BaseSettings,
allowing configuration through environment variables with sensible defaults.
"""

from .settings import (
    AppSettings,
    LLMSettings,
    ExecutionSettings,
    MessagingSettings,
    ServerSettings,
    StorageSettings,
    MonitoringSettings,
    get_settings,
    reset_settings,
    to_model_config,
    to_retry_policy,
    to_execution_config,
)

# Path configurations
from .paths import (
    BASE_DIR,
    FILES_DIR,
    PROJECTS_DIR,
    EXAMPLES_DIR,
    UPLOAD_DIR,
    RESULT_DIR,
    CONVERSATION_LOG_DIR,
    PROMPT_DIR,
    DATA_DIR,
    STATE_DB_PATH,
    EVENTS_DB_PATH,
    ensure_directories_exist,
)

# Service configurations
from .services import (
    VALID_LLM_SERVICES,
    LLM_SERVICE_TYPES,
    normalize_service_name,
    is_llm_service,
    api_service_type_to_llm_service,
    llm_service_to_api_service_type,
    get_llm_service_types,
    get_non_llm_service_types,
    is_valid_llm_service,
    is_valid_api_service_type,
)

# System limits
from .limits import (
    DEFAULT_TIMEOUT,
    MAX_EXECUTION_TIMEOUT,
    DEFAULT_HTTP_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    RETRY_BACKOFF_FACTOR,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_ITERATIONS,
    MAX_NODE_EXECUTIONS,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
)

__all__ = [
    # Settings
    "AppSettings",
    "LLMSettings",
    "ExecutionSettings",
    "MessagingSettings",
    "ServerSettings",
    "StorageSettings",
    "MonitoringSettings",
    "get_settings",
    "reset_settings",
    "to_model_config",
    "to_retry_policy",
    "to_execution_config",
    # Paths
    "BASE_DIR",
    "FILES_DIR",
    "PROJECTS_DIR",
    "EXAMPLES_DIR",
    "UPLOAD_DIR",
    "RESULT_DIR",
    "CONVERSATION_LOG_DIR",
    "PROMPT_DIR",
    "DATA_DIR",
    "STATE_DB_PATH",
    "EVENTS_DB_PATH",
    "ensure_directories_exist",
    # Services
    "VALID_LLM_SERVICES",
    "LLM_SERVICE_TYPES",
    "normalize_service_name",
    "is_llm_service",
    "api_service_type_to_llm_service",
    "llm_service_to_api_service_type",
    "get_llm_service_types",
    "get_non_llm_service_types",
    "is_valid_llm_service",
    "is_valid_api_service_type",
    # Limits
    "DEFAULT_TIMEOUT",
    "MAX_EXECUTION_TIMEOUT",
    "DEFAULT_HTTP_TIMEOUT",
    "MAX_RETRIES",
    "RETRY_DELAY",
    "RETRY_BACKOFF_FACTOR",
    "MAX_FILE_SIZE",
    "ALLOWED_EXTENSIONS",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "MAX_ITERATIONS",
    "MAX_NODE_EXECUTIONS",
    "LOG_FORMAT",
    "LOG_DATE_FORMAT",
]