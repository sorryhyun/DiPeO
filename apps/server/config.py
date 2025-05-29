from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(
    os.getenv("BASE_DIR",
              Path(__file__).resolve().parents[2].as_posix())
).resolve()

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

RESULT_DIR = BASE_DIR / "results"
RESULT_DIR.mkdir(exist_ok=True)

CONVERSATION_LOG_DIR = BASE_DIR / "conversation_logs"
CONVERSATION_LOG_DIR.mkdir(exist_ok=True)