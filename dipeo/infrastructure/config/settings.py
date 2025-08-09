"""Centralized configuration management for DiPeO infrastructure."""

import os
from enum import Enum
from pathlib import Path
from typing import Any


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings:
    def __init__(self):
        self.environment = self._get_environment()
        self.base_dir = self._get_base_dir()

        self.files_dir = self.base_dir / "files"
        self.uploads_dir = self.files_dir / "uploads"
        self.results_dir = self.files_dir / "results"
        self.diagrams_dir = self.files_dir / "diagrams"
        self.conversation_logs_dir = self.files_dir / "conversation_logs"
        self.prompts_dir = self.files_dir / "prompts"
        self.apikeys_file = self.files_dir / "apikeys.json"

        self.data_dir = self.base_dir / ".data"
        self.state_db_path = self.data_dir / "dipeo_state.db"
        self.events_db_path = self.data_dir / "dipeo_events.db"

        self.server_host = os.getenv("DIPEO_HOST", "0.0.0.0")
        self.server_port = int(os.getenv("DIPEO_PORT", "8000"))
        self.workers = int(os.getenv("DIPEO_WORKERS", "4"))
        self.log_level = os.getenv("DIPEO_LOG_LEVEL", "INFO")

        self.default_llm_model = os.getenv("DIPEO_DEFAULT_LLM_MODEL", "gpt-4.1-nano")
        self.llm_timeout = int(os.getenv("DIPEO_LLM_TIMEOUT", "300"))
        self.llm_max_retries = int(os.getenv("DIPEO_LLM_MAX_RETRIES", "3"))
        self.llm_retry_min_wait = float(os.getenv("DIPEO_LLM_RETRY_MIN_WAIT", "4.0"))
        self.llm_retry_max_wait = float(os.getenv("DIPEO_LLM_RETRY_MAX_WAIT", "10.0"))

        self.api_max_retries = int(os.getenv("DIPEO_API_MAX_RETRIES", "3"))
        self.api_retry_delay = float(os.getenv("DIPEO_API_RETRY_DELAY", "1.0"))
        self.api_timeout = int(os.getenv("DIPEO_API_TIMEOUT", "30"))

        self.execution_timeout = int(os.getenv("DIPEO_EXECUTION_TIMEOUT", "3600"))
        self.node_timeout = int(os.getenv("DIPEO_NODE_TIMEOUT", "300"))
        self.parallel_execution = (
            os.getenv("DIPEO_PARALLEL_EXECUTION", "true").lower() == "true"
        )
        self.node_ready_poll_interval = float(os.getenv("DIPEO_NODE_READY_POLL_INTERVAL", "0.01"))
        self.node_ready_max_polls = int(os.getenv("DIPEO_NODE_READY_MAX_POLLS", "100"))
        
        self.event_queue_size = int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "50000"))
        self.monitoring_queue_size = int(os.getenv("DIPEO_MONITORING_QUEUE_SIZE", "50000"))
        self.batch_broadcast_warning_threshold = float(
            os.getenv("DIPEO_BATCH_BROADCAST_WARNING_THRESHOLD", "0.2")
        )
        self.batch_max_size = int(os.getenv("DIPEO_BATCH_MAX_SIZE", "50"))
        self.batch_interval = float(os.getenv("DIPEO_BATCH_INTERVAL", "0.05"))

        self.cors_origins = self._parse_list(os.getenv("DIPEO_CORS_ORIGINS", "*"))
        self.allowed_file_extensions = self._parse_list(
            os.getenv(
                "DIPEO_ALLOWED_FILE_EXTENSIONS",
                ".txt,.json,.yaml,.yml,.md,.csv,.png,.jpg,.jpeg,.gif",
            )
        )
        self.max_upload_size = int(
            os.getenv("DIPEO_MAX_UPLOAD_SIZE", str(10 * 1024 * 1024))
        )

        self.enable_monitoring = (
            os.getenv("DIPEO_ENABLE_MONITORING", "false").lower() == "true"
        )
        self.enable_debug_mode = os.getenv("DIPEO_DEBUG", "false").lower() == "true"
        
        self.auto_prepend_conversation = (
            os.getenv("DIPEO_AUTO_PREPEND_CONVERSATION", "true").lower() == "true"
        )
        self.conversation_context_limit = int(
            os.getenv("DIPEO_CONVERSATION_CONTEXT_LIMIT", "10")
        )

        self._validate()

    def _get_environment(self) -> Environment:
        env = os.getenv("DIPEO_ENV", "development").lower()
        try:
            return Environment(env)
        except ValueError:
            return Environment.DEVELOPMENT

    def _get_base_dir(self) -> Path:
        if base_dir := os.getenv("DIPEO_BASE_DIR"):
            return Path(base_dir)

        # Locate project root using pyproject.toml + dipeo directory markers
        current = Path.cwd()
        while current != current.parent:
            if (current / "pyproject.toml").exists() and (current / "dipeo").exists():
                return current
            current = current.parent

        return Path.cwd()

    def _parse_list(self, value: str) -> list[str]:
        if not value or value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]

    def _validate(self):
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

        if not 1 <= self.server_port <= 65535:
            raise ValueError(f"Invalid port number: {self.server_port}")

        if self.workers < 1:
            raise ValueError(f"Workers must be at least 1, got {self.workers}")
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

        if self.max_upload_size <= 0:
            raise ValueError(
                f"max_upload_size must be positive, got {self.max_upload_size}"
            )

    def to_dict(self) -> dict[str, Any]:
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
            "conversation": {
                "auto_prepend": self.auto_prepend_conversation,
                "context_limit": self.conversation_context_limit,
            },
        }

    def get_environment_config(self) -> dict[str, Any]:
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


settings = Settings()


def get_settings() -> Settings:
    return settings


def reload_settings():
    global settings
    settings = Settings()
