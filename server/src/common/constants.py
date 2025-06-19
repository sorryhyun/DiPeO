"""
Shared domain constants used across the system.
"""
from typing import Final, Dict, Set
from src.__generated__.models import LLMService

# API Configuration
API_BASE_PATH: Final[str] = "/api"

# LLM Default Configuration
DEFAULT_MAX_TOKENS: Final[int] = 4096
DEFAULT_TEMPERATURE: Final[float] = 0.7

# File Extensions
SUPPORTED_DOC_EXTENSIONS: Final[Set[str]] = {".txt", ".md", ".docx", ".pdf"}
SUPPORTED_CODE_EXTENSIONS: Final[Set[str]] = {".py", ".js", ".ts", ".json", ".yaml", ".yml"}
SUPPORTED_DIAGRAM_EXTENSIONS: Final[Set[str]] = {".json", ".yaml", ".yml"}

# Service name mapping for normalization
SERVICE_TO_PROVIDER_MAP: Final[Dict[str, str]] = {
    "openai": "openai",
    "chatgpt": "openai",
    "claude": "anthropic",
    "anthropic": "anthropic",
    "gemini": "google",
    "google": "google",
    "grok": "xai",
    "xai": "xai",
    "bedrock": "bedrock",
    "vertex": "vertex",
    "deepseek": "deepseek"
}

# Provider to LLM service enum mapping
PROVIDER_TO_ENUM_MAP: Final[Dict[str, LLMService]] = {
    "openai": LLMService.OPENAI,
    "anthropic": LLMService.ANTHROPIC,
    "google": LLMService.GOOGLE,
    "xai": LLMService.GROK,
    "bedrock": LLMService.BEDROCK,
    "vertex": LLMService.VERTEX,
    "deepseek": LLMService.DEEPSEEK
}

# Default service when none specified
DEFAULT_SERVICE: Final[str] = "openai"

# Execution defaults
DEFAULT_EXECUTION_TIMEOUT: Final[int] = 3600  # 1 hour in seconds
DEFAULT_MAX_ITERATIONS: Final[int] = 100

# Memory defaults
DEFAULT_MEMORY_LIMIT: Final[int] = 100  # Maximum number of memories to retain
DEFAULT_CONTEXT_WINDOW: Final[int] = 10  # Number of recent messages to include in context