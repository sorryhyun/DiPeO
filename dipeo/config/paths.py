"""File system paths configuration for DiPeO."""

import os
import sys
from pathlib import Path


# Check if we're running as a PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR: Path = Path(sys.executable).parent.resolve()
else:
    # Find project root by looking for root pyproject.toml
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists() and (current / "dipeo").exists():
            BASE_DIR: Path = current
            break
        current = current.parent
    else:
        BASE_DIR: Path = Path(
            os.getenv("DIPEO_BASE_DIR", Path(__file__).resolve().parents[2].as_posix())
        ).resolve()

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