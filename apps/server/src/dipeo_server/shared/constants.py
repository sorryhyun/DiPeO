"""
Shared domain constants used across the system.
"""

from typing import Final

from dipeo_core.constants import (
    BASE_DIR,
    normalize_service_name,
)
from dipeo_core.constants import (
    VALID_LLM_SERVICES as CORE_VALID_SERVICES,
)

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

# Additional server-specific valid services
VALID_LLM_SERVICES: Final[set[str]] = CORE_VALID_SERVICES | {"bedrock", "vertex", "deepseek"}

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

# Re-export for convenience
__all__ = [
    "API_BASE_PATH",
    "BASE_DIR",
    "DEFAULT_CONTEXT_WINDOW",
    "DEFAULT_EXECUTION_TIMEOUT",
    "DEFAULT_MAX_ITERATIONS",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MEMORY_LIMIT",
    "DEFAULT_SERVICE",
    "DEFAULT_TEMPERATURE",
    "SUPPORTED_CODE_EXTENSIONS",
    "SUPPORTED_DIAGRAM_EXTENSIONS",
    "SUPPORTED_DOC_EXTENSIONS",
    "VALID_LLM_SERVICES",
    "normalize_service_name",
]
