"""File system paths configuration for DiPeO."""

import os
import sys
from pathlib import Path

# Check if we're running as a PyInstaller bundle
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR: Path = Path(sys.executable).parent.resolve()
else:
    # Prefer environment variable if set
    env_base_dir = os.getenv("DIPEO_BASE_DIR")
    if env_base_dir:
        BASE_DIR: Path = Path(env_base_dir).resolve()
    else:
        # Auto-detect project root by looking for monorepo structure
        current = Path(__file__).resolve().parent
        while current != current.parent:
            # Check for monorepo markers: both apps/ and dipeo/ directories
            if (current / "apps").exists() and (current / "dipeo").exists():
                BASE_DIR: Path = current
                break
            # Fallback: check for root pyproject.toml with dipeo/
            if (current / "pyproject.toml").exists() and (current / "dipeo").exists():
                BASE_DIR: Path = current
                break
            current = current.parent
        else:
            # Ultimate fallback: 2 levels up from this file
            BASE_DIR: Path = Path(__file__).resolve().parents[2]

# Directory structure
FILES_DIR: Path = BASE_DIR / "files"
PROJECTS_DIR: Path = BASE_DIR / "projects"
EXAMPLES_DIR: Path = BASE_DIR / "examples"
UPLOAD_DIR: Path = FILES_DIR / "uploads"
RESULT_DIR: Path = FILES_DIR / "results"
CONVERSATION_LOG_DIR: Path = FILES_DIR / "conversation_logs"
PROMPT_DIR: Path = FILES_DIR / "prompts"

# DiPeO runtime directory for all generated/runtime data
DIPEO_DIR: Path = BASE_DIR / ".dipeo"

# Data directory for databases
DATA_DIR: Path = DIPEO_DIR / "data"
STATE_DB_PATH: Path = DATA_DIR / "dipeo_state.db"
EVENTS_DB_PATH: Path = DATA_DIR / "dipeo_events.db"

# Cache directory for temporary cached data
CACHE_DIR: Path = DIPEO_DIR / "cache"


def ensure_directories_exist() -> None:
    """Ensure all required directories exist."""
    for dir_path in [
        FILES_DIR,
        EXAMPLES_DIR,
        UPLOAD_DIR,
        RESULT_DIR,
        CONVERSATION_LOG_DIR,
        PROMPT_DIR,
        DIPEO_DIR,
        DATA_DIR,
        CACHE_DIR,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)
