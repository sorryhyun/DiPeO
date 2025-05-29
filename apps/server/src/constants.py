from enum import Enum
from typing import Final


class NodeType(Enum):
    START = "start"
    PERSON_JOB = "person_job"
    CONDITION = "condition" 
    DB = "db"
    JOB = "job"
    ENDPOINT = "endpoint"
    
    @classmethod
    def from_legacy(cls, node_type: str) -> 'NodeType':
        """Convert legacy node type strings to enum values."""
        mappings = {
            'startNode': cls.START,
            'personjobNode': cls.PERSON_JOB,
            'conditionNode': cls.CONDITION,
            'dbNode': cls.DB,
            'codeNode': cls.JOB,
            'jobNode': cls.JOB,
            'endpointNode': cls.ENDPOINT,
            'dbTargetNode': cls.ENDPOINT,  # DB Target was merged into Endpoint
        }
        if node_type in mappings:
            return mappings[node_type]
        try:
            return cls(node_type)
        except ValueError:
            raise ValueError(f"Unknown node type: {node_type}")

class DBBlockSubType(Enum):
    FIXED_PROMPT = "fixed_prompt"
    FILE = "file"
    CODE = "code"

class DBTargetSubType(Enum):
    LOCAL_FILE = "local_file"
    SQLITE = "sqlite"

class ContentType(Enum):
    VARIABLE = "variable"
    RAW_TEXT = "raw_text"
    CONVERSATION_STATE = "conversation_state"

class ContextCleaningRule(Enum):
    ON_EVERY_TURN = "on_every_turn"
    PRESERVE = "preserve"

class LLMService(Enum):
    CHATGPT = "chatgpt"
    OPENAI = "openai" 
    CLAUDE = "claude"
    GEMINI = "gemini"
    GROK = "grok"

API_BASE_PATH: Final[str] = "/api"
DEFAULT_MAX_TOKENS: Final[int] = 4096
DEFAULT_TEMPERATURE: Final[float] = 0.7

SUPPORTED_DOC_EXTENSIONS: Final[set[str]] = {".txt", ".md", ".docx", ".pdf"}
SUPPORTED_CODE_EXTENSIONS: Final[set[str]] = {".py", ".js", ".ts", ".json", ".yaml", ".yml"}

COST_RATES: Final[dict[str, dict[str, float]]] = {
    "chatgpt": {"input": 2.0, "output": 8.0, "cached": 0.5},
    "claude": {"input": 3.0, "output": 15.0},
    "gemini": {"input": 3.0, "output": 15.0}
}