"""Unified configuration module for DiPeO.

This module provides centralized configuration management using Pydantic BaseSettings,
allowing configuration through environment variables with sensible defaults.
"""

# System limits
from .limits import (
    ALLOWED_EXTENSIONS,
    DEFAULT_HTTP_TIMEOUT,
    DEFAULT_PAGE_SIZE,
    DEFAULT_TIMEOUT,
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    MAX_EXECUTION_TIMEOUT,
    MAX_FILE_SIZE,
    MAX_ITERATIONS,
    MAX_NODE_EXECUTIONS,
    MAX_PAGE_SIZE,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
    RETRY_DELAY,
)

# Path configurations
from .paths import (
    BASE_DIR,
    CONVERSATION_LOG_DIR,
    DATA_DIR,
    EVENTS_DB_PATH,
    EXAMPLES_DIR,
    FILES_DIR,
    PROJECTS_DIR,
    PROMPT_DIR,
    RESULT_DIR,
    STATE_DB_PATH,
    UPLOAD_DIR,
    ensure_directories_exist,
)

# Service configurations
from .services import (
    LLM_SERVICE_TYPES,
    VALID_LLM_SERVICES,
    api_service_type_to_llm_service,
    get_llm_service_types,
    get_non_llm_service_types,
    is_llm_service,
    is_valid_api_service_type,
    is_valid_llm_service,
    llm_service_to_api_service_type,
    normalize_service_name,
)
from .settings import (
    AppSettings,
    ExecutionSettings,
    LLMSettings,
    MessagingSettings,
    MonitoringSettings,
    ServerSettings,
    StorageSettings,
    get_settings,
    reset_settings,
    to_execution_config,
    to_model_config,
    to_retry_policy,
)

__all__ = [
    "ALLOWED_EXTENSIONS",
    # Paths
    "BASE_DIR",
    "CONVERSATION_LOG_DIR",
    "DATA_DIR",
    "DEFAULT_HTTP_TIMEOUT",
    "DEFAULT_PAGE_SIZE",
    # Limits
    "DEFAULT_TIMEOUT",
    "EVENTS_DB_PATH",
    "EXAMPLES_DIR",
    "FILES_DIR",
    "LLM_SERVICE_TYPES",
    "LOG_DATE_FORMAT",
    "LOG_FORMAT",
    "MAX_EXECUTION_TIMEOUT",
    "MAX_FILE_SIZE",
    "MAX_ITERATIONS",
    "MAX_NODE_EXECUTIONS",
    "MAX_PAGE_SIZE",
    "MAX_RETRIES",
    "PROJECTS_DIR",
    "PROMPT_DIR",
    "RESULT_DIR",
    "RETRY_BACKOFF_FACTOR",
    "RETRY_DELAY",
    "STATE_DB_PATH",
    "UPLOAD_DIR",
    # Services
    "VALID_LLM_SERVICES",
    # Settings
    "AppSettings",
    "ExecutionSettings",
    "LLMSettings",
    "MessagingSettings",
    "MonitoringSettings",
    "ServerSettings",
    "StorageSettings",
    "api_service_type_to_llm_service",
    "ensure_directories_exist",
    "get_llm_service_types",
    "get_non_llm_service_types",
    "get_settings",
    "is_llm_service",
    "is_valid_api_service_type",
    "is_valid_llm_service",
    "llm_service_to_api_service_type",
    "normalize_service_name",
    "reset_settings",
    "to_execution_config",
    "to_model_config",
    "to_retry_policy",
]
