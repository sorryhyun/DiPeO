"""Server configuration - imports path constants from dipeo.core."""

from dipeo.domain.constants import (
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
    "CONVERSATION_LOG_DIR",
    "DATA_DIR",
    "EVENTS_DB_PATH",
    "FILES_DIR",
    "PROMPT_DIR",
    "RESULT_DIR",
    "STATE_DB_PATH",
    "UPLOAD_DIR",
]
