"""Core constants shared across DiPeO components."""

import os
import sys
from pathlib import Path

# Project Base Directory
# Check if we're running as a PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle - use executable directory
    BASE_DIR: Path = Path(sys.executable).parent.resolve()
else:
    # Normal execution - find project root by looking for root pyproject.toml
    # Start from dipeo/core/constants.py and go up
    current = Path(__file__).resolve().parent
    while current != current.parent:
        # Check for root-level indicators
        if (current / "pyproject.toml").exists() and (current / "dipeo").exists():
            # This is the project root (has both pyproject.toml and dipeo directory)
            BASE_DIR: Path = current
            break
        current = current.parent
    else:
        # Fallback to environment variable or default
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
    "google",
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
    }

    return aliases.get(normalized, normalized)
