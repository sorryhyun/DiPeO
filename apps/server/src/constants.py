from enum import Enum
from typing import Final


class NodeType(Enum):
    START = "start"
    PERSON_JOB = "person_job"
    PERSON_BATCH_JOB = "person_batch_job"
    CONDITION = "condition" 
    DB = "db"
    JOB = "job"
    ENDPOINT = "endpoint"
    USER_RESPONSE = "user_response"
    NOTION = "notion"
    

class DBBlockSubType(Enum):
    FIXED_PROMPT = "fixed_prompt"
    FILE = "file"
    CODE = "code"


class ContentType(Enum):
    VARIABLE = "variable"
    RAW_TEXT = "raw_text"
    CONVERSATION_STATE = "conversation_state"

class ContextCleaningRule(Enum):
    ON_EVERY_TURN = "on_every_turn"
    UPON_REQUEST = "upon_request"
    NO_FORGET = "no_forget"

class LLMService(Enum):
    OPENAI = "openai" 
    CLAUDE = "claude"
    GEMINI = "gemini"
    GROK = "grok"

API_BASE_PATH: Final[str] = "/api"
DEFAULT_MAX_TOKENS: Final[int] = 4096
DEFAULT_TEMPERATURE: Final[float] = 0.7

SUPPORTED_DOC_EXTENSIONS: Final[set[str]] = {".txt", ".md", ".docx", ".pdf"}
SUPPORTED_CODE_EXTENSIONS: Final[set[str]] = {".py", ".js", ".ts", ".json", ".yaml", ".yml"}

# Service name mapping for normalization
SERVICE_TO_PROVIDER_MAP: Final[dict[str, str]] = {
    "openai": "openai",
    "chatgpt": "openai",
    "claude": "anthropic",
    "anthropic": "anthropic",
    "gemini": "google",
    "google": "google",
    "grok": "xai",
    "xai": "xai"
}

# Provider to LLM service enum mapping
PROVIDER_TO_ENUM_MAP: Final[dict[str, LLMService]] = {
    "openai": LLMService.OPENAI,
    "anthropic": LLMService.CLAUDE,
    "google": LLMService.GEMINI,
    "xai": LLMService.GROK
}

# Default service when none specified
DEFAULT_SERVICE: Final[str] = "openai"