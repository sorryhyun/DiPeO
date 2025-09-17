"""Unified application configuration using Pydantic BaseSettings.

This module provides centralized configuration management for DiPeO,
consolidating infrastructure and domain configuration with sensible defaults
and environment variable overrides.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    """LLM provider configuration settings."""

    default_model: str = Field(
        default="gpt-5-nano-2025-08-07",
        env="DIPEO_DEFAULT_LLM_MODEL",
        description="Default LLM model to use",
    )
    timeout_s: int = Field(
        default=100, env="DIPEO_LLM_TIMEOUT", description="LLM request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        env="DIPEO_LLM_MAX_RETRIES",
        description="Maximum retry attempts for LLM requests",
    )
    temperature: float = Field(
        default=0.2,
        env="DIPEO_LLM_TEMPERATURE",
        description="Default temperature for LLM responses",
    )
    max_tokens: int | None = Field(
        default=128000, env="DIPEO_LLM_MAX_TOKENS", description="Maximum tokens for LLM responses"
    )
    person_job_temperature: float = Field(
        default=0.2,
        env="DIPEO_PERSON_JOB_TEMPERATURE",
        description="Temperature for PersonJob node LLM calls",
    )
    person_job_max_tokens: int = Field(
        default=128000,
        env="DIPEO_PERSON_JOB_MAX_TOKENS",
        description="Max tokens for PersonJob node LLM calls",
    )

    class Config:
        env_prefix = "DIPEO_LLM_"
        extra = "ignore"


class ExecutionSettings(BaseSettings):
    """Execution engine configuration settings."""

    engine_timeout_s: int = Field(
        default=3600, env="DIPEO_EXECUTION_TIMEOUT", description="Maximum execution time in seconds"
    )
    node_timeout_s: int = Field(
        default=100, env="DIPEO_NODE_TIMEOUT", description="Per-node execution timeout in seconds"
    )
    parallelism: int = Field(
        default=15,
        env="DIPEO_EXECUTION_PARALLELISM",
        description="Maximum parallel node executions",
    )
    enable_parallel: bool = Field(
        default=True, env="DIPEO_PARALLEL_EXECUTION", description="Enable parallel node execution"
    )
    max_iterations: int = Field(
        default=150, env="DIPEO_MAX_ITERATIONS", description="Maximum iterations for loop nodes"
    )

    class Config:
        env_prefix = "DIPEO_EXECUTION_"
        extra = "ignore"


class MessagingSettings(BaseSettings):
    """Message routing and event bus configuration settings."""

    batch_max: int = Field(
        default=25, env="DIPEO_MSG_BATCH_MAX", description="Maximum events per batch"
    )
    batch_interval_ms: int = Field(
        default=50, env="DIPEO_MSG_BATCH_INTERVAL", description="Batch interval in milliseconds"
    )
    buffer_max_per_exec: int = Field(
        default=50, env="DIPEO_MSG_BUFFER_MAX", description="Maximum buffered events per execution"
    )
    buffer_ttl_s: int = Field(
        default=300, env="DIPEO_MSG_BUFFER_TTL", description="Event buffer TTL in seconds"
    )
    redis_url: str | None = Field(
        default=None, env="DIPEO_REDIS_URL", description="Redis URL for distributed messaging"
    )
    max_queue_size: int = Field(
        default=10000,
        env="DIPEO_MSG_MAX_QUEUE_SIZE",
        description="Maximum queue size per connection",
    )
    broadcast_warning_threshold_s: float = Field(
        default=0.5,
        env="DIPEO_MSG_BROADCAST_WARNING_THRESHOLD",
        description="Warning threshold for slow broadcasts in seconds",
    )
    ws_keepalive_sec: int = Field(
        default=25,
        env="DIPEO_WS_KEEPALIVE_SEC",
        description="WebSocket keepalive interval in seconds (0 to disable)",
    )

    class Config:
        env_prefix = "DIPEO_MSG_"
        extra = "ignore"


class ServerSettings(BaseSettings):
    """Server configuration settings."""

    host: str = Field(default="0.0.0.0", env="DIPEO_HOST", description="Server host address")
    port: int = Field(default=8000, env="DIPEO_PORT", description="Server port")
    workers: int = Field(default=2, env="DIPEO_WORKERS", description="Number of server workers")
    reload: bool = Field(
        default=False, env="DIPEO_RELOAD", description="Enable auto-reload in development"
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="DIPEO_CORS_ORIGINS",
        description="Allowed CORS origins",
    )

    class Config:
        env_prefix = "DIPEO_"
        extra = "ignore"


class StorageSettings(BaseSettings):
    """Storage configuration settings."""

    base_dir: str = Field(
        default_factory=lambda: str(Path(__file__).resolve().parents[2]),
        env="DIPEO_BASE_DIR",
        description="Base directory for DiPeO",
    )
    data_dir: str = Field(
        default="files",
        env="DIPEO_DATA_DIR",
        description="Data files directory (relative to base_dir)",
    )
    logs_dir: str = Field(
        default=".logs", env="DIPEO_LOGS_DIR", description="Logs directory (relative to base_dir)"
    )
    temp_dir: str = Field(
        default="temp",
        env="DIPEO_TEMP_DIR",
        description="Temporary files directory (relative to base_dir)",
    )
    diagrams_dir: str = Field(
        default="examples",
        env="DIPEO_DIAGRAMS_DIR",
        description="Diagrams directory (relative to base_dir)",
    )

    class Config:
        env_prefix = "DIPEO_"
        extra = "ignore"


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration settings."""

    enable_monitoring: bool = Field(
        default=False, env="DIPEO_ENABLE_MONITORING", description="Enable execution monitoring"
    )
    enable_metrics: bool = Field(
        default=True, env="DIPEO_ENABLE_METRICS", description="Enable metrics collection"
    )
    metrics_interval_s: int = Field(
        default=60,
        env="DIPEO_METRICS_INTERVAL",
        description="Metrics collection interval in seconds",
    )
    log_level: str = Field(default="INFO", env="DIPEO_LOG_LEVEL", description="Logging level")
    debug: bool = Field(default=False, env="DIPEO_DEBUG", description="Enable debug mode")

    class Config:
        env_prefix = "DIPEO_"
        extra = "ignore"


class DependencyInjectionSettings(BaseSettings):
    """Dependency injection safety and auditing configuration settings."""

    # Override Control
    allow_override: bool = Field(
        default=False,
        env="DIPEO_DI_ALLOW_OVERRIDE",
        description="Allow service overrides (auto-enabled in dev/test environments)",
    )

    # Freezing Behavior
    freeze_after_boot: bool = Field(
        default=True,
        env="DIPEO_DI_FREEZE_AFTER_BOOT",
        description="Freeze registry after application bootstrap completes",
    )
    auto_freeze_in_production: bool = Field(
        default=True,
        env="DIPEO_DI_AUTO_FREEZE_PRODUCTION",
        description="Automatically freeze registry in production environment",
    )

    # Audit Trail
    enable_audit: bool = Field(
        default=True,
        env="DIPEO_DI_ENABLE_AUDIT",
        description="Enable audit trail for service registrations",
    )
    audit_max_records: int = Field(
        default=1000,
        env="DIPEO_DI_AUDIT_MAX_RECORDS",
        description="Maximum audit records to keep in memory",
    )

    # Safety Features
    require_override_reason_in_prod: bool = Field(
        default=True,
        env="DIPEO_DI_REQUIRE_OVERRIDE_REASON_PROD",
        description="Require override reason for production overrides",
    )
    validate_dependencies_on_boot: bool = Field(
        default=True,
        env="DIPEO_DI_VALIDATE_DEPENDENCIES",
        description="Validate service dependencies during bootstrap",
    )

    # Development Features
    allow_temporary_overrides: bool = Field(
        default=True,
        env="DIPEO_DI_ALLOW_TEMP_OVERRIDES",
        description="Allow temporary service overrides in test contexts",
    )
    strict_final_services: bool = Field(
        default=True,
        env="DIPEO_DI_STRICT_FINAL_SERVICES",
        description="Strictly enforce final service constraints",
    )

    class Config:
        env_prefix = "DIPEO_DI_"
        extra = "ignore"


class AppSettings(BaseSettings):
    """Main application configuration combining all settings."""

    env: str = Field(
        default="development",
        env="DIPEO_ENV",
        description="Environment (development, testing, production)",
    )

    # Nested settings
    llm: LLMSettings = LLMSettings()
    execution: ExecutionSettings = ExecutionSettings()
    messaging: MessagingSettings = MessagingSettings()
    server: ServerSettings = ServerSettings()
    storage: StorageSettings = StorageSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    dependency_injection: DependencyInjectionSettings = DependencyInjectionSettings()

    class Config:
        env_prefix = "DIPEO_"
        extra = "ignore"
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Get the application settings singleton.

    Returns:
        AppSettings: The application settings instance
    """
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def reset_settings() -> None:
    """Reset the settings singleton (mainly for testing)."""
    global _settings
    _settings = None


# Domain value object adapters
def to_model_config(settings: AppSettings) -> dict:
    """Convert AppSettings to domain ModelConfig value object format.

    Args:
        settings: Application settings

    Returns:
        Dictionary compatible with ModelConfig constructor
    """
    return {
        "provider": "openai",  # Default provider
        "model": settings.llm.default_model,
        "temperature": settings.llm.temperature,
        "max_tokens": settings.llm.max_tokens,
        "timeout": settings.llm.timeout_s,
        "max_retries": settings.llm.max_retries,
    }


def to_retry_policy(settings: AppSettings) -> dict:
    """Convert AppSettings to domain RetryPolicy value object format.

    Args:
        settings: Application settings

    Returns:
        Dictionary compatible with RetryPolicy constructor
    """
    return {
        "max_attempts": settings.llm.max_retries,
        "initial_delay": 1.0,
        "max_delay": 60.0,
        "exponential_base": 2.0,
    }


def to_execution_config(settings: AppSettings) -> dict:
    """Convert AppSettings to execution configuration format.

    Args:
        settings: Application settings

    Returns:
        Dictionary compatible with execution engine configuration
    """
    return {
        "timeout": settings.execution.engine_timeout_s,
        "node_timeout": settings.execution.node_timeout_s,
        "max_parallel": settings.execution.parallelism,
        "enable_parallel": settings.execution.enable_parallel,
        "max_iterations": settings.execution.max_iterations,
    }
