"""Core constants shared across DiPeO components."""

import os
from pathlib import Path

# Project Base Directory
# Go up from dipeo/core/constants.py to project root
BASE_DIR: Path = Path(
    os.getenv("DIPEO_BASE_DIR", Path(__file__).resolve().parents[2].as_posix())
).resolve()

# Unified file storage directories (no mkdir here - let apps create as needed)
FILES_DIR: Path = BASE_DIR / "files"
UPLOAD_DIR: Path = FILES_DIR / "uploads"
RESULT_DIR: Path = FILES_DIR / "results"
CONVERSATION_LOG_DIR: Path = FILES_DIR / "conversation_logs"
PROMPT_DIR: Path = FILES_DIR / "prompts"

# Database directory (no mkdir here - let apps create as needed)
DATA_DIR: Path = BASE_DIR / ".data"
STATE_DB_PATH: Path = DATA_DIR / "dipeo_state.db"
EVENTS_DB_PATH: Path = DATA_DIR / "dipeo_events.db"

# Valid LLM services
VALID_LLM_SERVICES = {
    "openai",
    "anthropic",
    "gemini",
    "grok",
    "google",
    "x",
}

# Timeouts
DEFAULT_TIMEOUT = 30.0  # seconds
MAX_EXECUTION_TIMEOUT = 600.0  # 10 minutes
DEFAULT_HTTP_TIMEOUT = 10.0  # seconds

# Retries
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF_FACTOR = 2.0

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# File system
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml", ".txt", ".md", ".py", ".js", ".ts"}

# API
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000

# Execution
MAX_ITERATIONS = 100
MAX_NODE_EXECUTIONS = 1000


def ensure_directories_exist() -> None:
    """Ensure all required directories exist."""
    for dir_path in [
        FILES_DIR,
        UPLOAD_DIR,
        RESULT_DIR,
        CONVERSATION_LOG_DIR,
        PROMPT_DIR,
        DATA_DIR,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)


def normalize_service_name(service: str) -> str:
    """Normalize service name to canonical form."""
    normalized = service.lower().strip()

    # Service aliases
    aliases = {
        "claude": "anthropic",
        "chatgpt": "openai",
        "gpt": "openai",
        "gpt-4": "openai",
        "gpt-3.5": "openai",
        "google": "gemini",
        "x": "grok",
        "xai": "grok",
        "x-ai": "grok",
    }

    return aliases.get(normalized, normalized)
