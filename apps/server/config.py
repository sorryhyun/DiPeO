import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(
    os.getenv("BASE_DIR",
              Path(__file__).resolve().parents[2].as_posix())
).resolve()

# Unified file storage under files/ directory
FILES_DIR = BASE_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)

UPLOAD_DIR = FILES_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

RESULT_DIR = FILES_DIR / "results"
RESULT_DIR.mkdir(exist_ok=True)

CONVERSATION_LOG_DIR = FILES_DIR / "conversation_logs"
CONVERSATION_LOG_DIR.mkdir(exist_ok=True)

PROMPT_DIR = FILES_DIR / "prompts"
PROMPT_DIR.mkdir(exist_ok=True)

YAML_DIAGRAM_DIR = FILES_DIR / "yaml_diagrams"
YAML_DIAGRAM_DIR.mkdir(exist_ok=True)

# Database directory
DATA_DIR = Path(__file__).parent / ".data"
DATA_DIR.mkdir(exist_ok=True)

# Database paths
STATE_DB_PATH = DATA_DIR / "dipeo_state.db"
EVENTS_DB_PATH = DATA_DIR / "dipeo_events.db"
