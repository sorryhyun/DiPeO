"""Server configuration - imports path constants from dipeo_core."""

from dipeo_core.constants import (
    BASE_DIR,
    CONVERSATION_LOG_DIR,
    DATA_DIR,
    EVENTS_DB_PATH,
    FILES_DIR,
    PROMPT_DIR,
    RESULT_DIR,
    STATE_DB_PATH,
    UPLOAD_DIR,
)

# Re-export for backward compatibility
__all__ = [
    "BASE_DIR",
    "FILES_DIR",
    "UPLOAD_DIR",
    "RESULT_DIR",
    "CONVERSATION_LOG_DIR",
    "PROMPT_DIR",
    "DATA_DIR",
    "STATE_DB_PATH",
    "EVENTS_DB_PATH",
]