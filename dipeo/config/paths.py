"""File system paths configuration for DiPeO."""

import os
import sys
from pathlib import Path

# Check if we're running as a PyInstaller bundle
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR: Path = Path(sys.executable).parent.resolve()
else:
    # First check for explicit environment variable
    if env_base := os.getenv("DIPEO_BASE_DIR"):
        BASE_DIR: Path = Path(env_base).resolve()
    else:
        # Find project root by looking for monorepo structure (apps/ and dipeo/ directories)
        current = Path(__file__).resolve().parent
        while current != current.parent:
            # Look for monorepo root with apps/ and dipeo/ directories
            if (current / "apps").exists() and (current / "dipeo").exists():
                BASE_DIR: Path = current
                break
            # Fallback: root pyproject.toml with dipeo directory
            if (current / "pyproject.toml").exists() and (current / "dipeo").exists():
                BASE_DIR: Path = current
                break
            current = current.parent
        else:
            # Ultimate fallback: 2 directories up from this file
            BASE_DIR: Path = Path(__file__).resolve().parents[2]

# Directory structure
FILES_DIR: Path = BASE_DIR / "files"
PROJECTS_DIR: Path = BASE_DIR / "projects"
EXAMPLES_DIR: Path = BASE_DIR / "examples"
UPLOAD_DIR: Path = FILES_DIR / "uploads"
RESULT_DIR: Path = FILES_DIR / "results"
CONVERSATION_LOG_DIR: Path = FILES_DIR / "conversation_logs"
PROMPT_DIR: Path = FILES_DIR / "prompts"

# Data directory for databases
DATA_DIR: Path = BASE_DIR / ".data"
STATE_DB_PATH: Path = DATA_DIR / "dipeo_state.db"
EVENTS_DB_PATH: Path = DATA_DIR / "dipeo_events.db"


def ensure_directories_exist() -> None:
    """Ensure all required directories exist."""
    for dir_path in [
        FILES_DIR,
        EXAMPLES_DIR,
        UPLOAD_DIR,
        RESULT_DIR,
        CONVERSATION_LOG_DIR,
        PROMPT_DIR,
        DATA_DIR,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)
