"""
Shared domain constants used across the system.
"""

import os
from pathlib import Path
from typing import Final

# Project Base Directory
BASE_DIR: Final[Path] = Path(
    os.getenv("DIPEO_BASE_DIR", Path(__file__).resolve().parents[5].as_posix())
).resolve()

# API Configuration
API_BASE_PATH: Final[str] = "/api"

# LLM Default Configuration
DEFAULT_MAX_TOKENS: Final[int] = 4096
DEFAULT_TEMPERATURE: Final[float] = 0.7

# File Extensions
SUPPORTED_DOC_EXTENSIONS: Final[set[str]] = {".txt", ".md", ".docx", ".pdf"}
SUPPORTED_CODE_EXTENSIONS: Final[set[str]] = {
    ".py",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
}
SUPPORTED_DIAGRAM_EXTENSIONS: Final[set[str]] = {".json", ".yaml", ".yml"}

# Service aliases (only non-identity mappings)
SERVICE_ALIASES: Final[dict[str, str]] = {
    "chatgpt": "openai",
    "claude": "anthropic",
    "gemini": "google",
    "xai": "grok",
}

# Valid LLM services
VALID_LLM_SERVICES: Final[set[str]] = {
    "openai",
    "anthropic",
    "google",
    "grok",
    "bedrock",
    "vertex",
    "deepseek",
}

# Default service when none specified
DEFAULT_SERVICE: Final[str] = "openai"

# Execution defaults
DEFAULT_EXECUTION_TIMEOUT: Final[int] = 3600  # 1 hour in seconds
DEFAULT_MAX_ITERATIONS: Final[int] = 100

# Memory defaults
DEFAULT_MEMORY_LIMIT: Final[int] = 100  # Maximum number of memories to retain
DEFAULT_CONTEXT_WINDOW: Final[int] = (
    10  # Number of recent messages to include in context
)


def normalize_service_name(service: str) -> str:
    """Normalize service name to provider name using centralized mapping.

    Args:
        service: The service name to normalize

    Returns:
        The normalized service name
    """
    normalized = (service or DEFAULT_SERVICE).lower()
    return SERVICE_ALIASES.get(normalized, normalized)
