"""Centralized configuration management for DiPeO infrastructure."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings:
    def __init__(self):
        self.environment = self._get_environment()
        self.base_dir = self._get_base_dir()

        # File storage paths
        self.files_dir = self.base_dir / "files"
        self.uploads_dir = self.files_dir / "uploads"
        self.results_dir = self.files_dir / "results"
        self.diagrams_dir = self.files_dir / "diagrams"
        self.conversation_logs_dir = self.files_dir / "conversation_logs"
        self.prompts_dir = self.files_dir / "prompts"
        self.apikeys_file = self.files_dir / "apikeys.json"

        # Database paths
        self.data_dir = self.base_dir / ".data"
        self.state_db_path = self.data_dir / "dipeo_state.db"
        self.events_db_path = self.data_dir / "dipeo_events.db"

        # Server settings
        self.server_host = os.getenv("DIPEO_HOST", "0.0.0.0")
        self.server_port = int(os.getenv("DIPEO_PORT", "8000"))
        self.workers = int(os.getenv("DIPEO_WORKERS", "4"))
        self.log_level = os.getenv("DIPEO_LOG_LEVEL", "INFO")

        # LLM settings
        self.default_llm_model = os.getenv("DIPEO_DEFAULT_LLM_MODEL", "gpt-4.1-nano")
        self.llm_timeout = int(os.getenv("DIPEO_LLM_TIMEOUT", "300"))
        self.llm_max_retries = int(os.getenv("DIPEO_LLM_MAX_RETRIES", "3"))
        self.llm_retry_min_wait = float(os.getenv("DIPEO_LLM_RETRY_MIN_WAIT", "4.0"))
        self.llm_retry_max_wait = float(os.getenv("DIPEO_LLM_RETRY_MAX_WAIT", "10.0"))

        # API settings
        self.api_max_retries = int(os.getenv("DIPEO_API_MAX_RETRIES", "3"))
        self.api_retry_delay = float(os.getenv("DIPEO_API_RETRY_DELAY", "1.0"))
        self.api_timeout = int(os.getenv("DIPEO_API_TIMEOUT", "30"))

        # Execution settings
        self.execution_timeout = int(os.getenv("DIPEO_EXECUTION_TIMEOUT", "3600"))
        self.node_timeout = int(os.getenv("DIPEO_NODE_TIMEOUT", "300"))
        self.parallel_execution = (
            os.getenv("DIPEO_PARALLEL_EXECUTION", "true").lower() == "true"
        )
        self.node_ready_poll_interval = float(os.getenv("DIPEO_NODE_READY_POLL_INTERVAL", "0.01"))
        self.node_ready_max_polls = int(os.getenv("DIPEO_NODE_READY_MAX_POLLS", "100"))

        # Security settings
        self.cors_origins = self._parse_list(os.getenv("DIPEO_CORS_ORIGINS", "*"))
        self.allowed_file_extensions = self._parse_list(
            os.getenv(
                "DIPEO_ALLOWED_FILE_EXTENSIONS",
                ".txt,.json,.yaml,.yml,.md,.csv,.png,.jpg,.jpeg,.gif",
            )
        )
        self.max_upload_size = int(
            os.getenv("DIPEO_MAX_UPLOAD_SIZE", str(10 * 1024 * 1024))
        )  # 10MB default

        # Feature flags
        self.enable_monitoring = (
            os.getenv("DIPEO_ENABLE_MONITORING", "false").lower() == "true"
        )
        self.enable_debug_mode = os.getenv("DIPEO_DEBUG", "false").lower() == "true"

        # Validate configuration
        self._validate()

    def _get_environment(self) -> Environment:
        env = os.getenv("DIPEO_ENV", "development").lower()
        try:
            return Environment(env)
        except ValueError:
            return Environment.DEVELOPMENT

    def _get_base_dir(self) -> Path:
        # Try environment variable first
        if base_dir := os.getenv("DIPEO_BASE_DIR"):
            return Path(base_dir)

        # Try to find project root by looking for pyproject.toml
        current = Path.cwd()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent

        # Default to current directory
        return Path.cwd()

    def _parse_list(self, value: str) -> list[str]:
        if not value or value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]

    def _validate(self):
        # Ensure directories exist
        for dir_path in [
            self.files_dir,
            self.uploads_dir,
            self.results_dir,
            self.diagrams_dir,
            self.conversation_logs_dir,
            self.prompts_dir,
            self.data_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Validate port range
        if not 1 <= self.server_port <= 65535:
            raise ValueError(f"Invalid port number: {self.server_port}")

        # Validate workers
        if self.workers < 1:
            raise ValueError(f"Workers must be at least 1, got {self.workers}")

        # Validate timeouts
        for timeout_name, timeout_value in [
            ("llm_timeout", self.llm_timeout),
            ("api_timeout", self.api_timeout),
            ("execution_timeout", self.execution_timeout),
            ("node_timeout", self.node_timeout),
        ]:
            if timeout_value <= 0:
                raise ValueError(
                    f"{timeout_name} must be positive, got {timeout_value}"
                )

        # Validate file size
        if self.max_upload_size <= 0:
            raise ValueError(
                f"max_upload_size must be positive, got {self.max_upload_size}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment": self.environment.value,
            "base_dir": str(self.base_dir),
            "server": {
                "host": self.server_host,
                "port": self.server_port,
                "workers": self.workers,
                "log_level": self.log_level,
            },
            "paths": {
                "files_dir": str(self.files_dir),
                "data_dir": str(self.data_dir),
                "state_db": str(self.state_db_path),
                "events_db": str(self.events_db_path),
            },
            "llm": {
                "default_model": self.default_llm_model,
                "timeout": self.llm_timeout,
                "max_retries": self.llm_max_retries,
                "retry_min_wait": self.llm_retry_min_wait,
                "retry_max_wait": self.llm_retry_max_wait,
            },
            "api": {
                "max_retries": self.api_max_retries,
                "retry_delay": self.api_retry_delay,
                "timeout": self.api_timeout,
            },
            "execution": {
                "timeout": self.execution_timeout,
                "node_timeout": self.node_timeout,
                "parallel": self.parallel_execution,
                "node_ready_poll_interval": self.node_ready_poll_interval,
                "node_ready_max_polls": self.node_ready_max_polls,
            },
            "security": {
                "cors_origins": self.cors_origins,
                "allowed_extensions": self.allowed_file_extensions,
                "max_upload_size": self.max_upload_size,
            },
            "features": {
                "monitoring": self.enable_monitoring,
                "debug_mode": self.enable_debug_mode,
            },
        }

    def get_environment_config(self) -> Dict[str, Any]:
        if self.environment == Environment.PRODUCTION:
            return {
                "log_level": "WARNING",
                "enable_debug_mode": False,
                "llm_max_retries": 5,
                "api_max_retries": 5,
            }
        elif self.environment == Environment.TESTING:
            return {
                "log_level": "DEBUG",
                "enable_debug_mode": True,
                "llm_timeout": 10,
                "api_timeout": 5,
                "execution_timeout": 60,
            }
        else:  # DEVELOPMENT
            return {
                "log_level": "DEBUG",
                "enable_debug_mode": True,
            }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    return settings


def reload_settings():
    global settings
    settings = Settings()
