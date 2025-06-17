"""
Shared domain enums used across multiple domains.
These are the core enumerations that define the vocabulary of the system.
"""
from enum import Enum


class NodeType(str, Enum):
    """Types of nodes available in the diagram system."""
    START = "start"
    PERSON_JOB = "person_job"
    CONDITION = "condition"
    JOB = "job"
    ENDPOINT = "endpoint"
    DB = "db"
    USER_RESPONSE = "user_response"
    NOTION = "notion"
    PERSON_BATCH_JOB = "person_batch_job"


class HandleDirection(str, Enum):
    """Direction of handles on nodes."""
    INPUT = "input"
    OUTPUT = "output"


class DataType(str, Enum):
    """Data types supported by the system."""
    ANY = "any"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class LLMService(str, Enum):
    """Supported LLM service providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROK = "grok"
    BEDROCK = "bedrock"
    VERTEX = "vertex"
    DEEPSEEK = "deepseek"


class ForgettingMode(str, Enum):
    """Memory forgetting modes for LLM interactions."""
    NO_FORGET = "no_forget"
    NONE = "none"
    ON_EVERY_TURN = "on_every_turn"
    UPON_REQUEST = "upon_request"
    
    @classmethod
    def _missing_(cls, value):
        """Handle legacy values."""
        if value == "no_forget":
            return cls.NONE
        return None


class DiagramFormat(str, Enum):
    """Supported diagram file formats."""
    NATIVE = "native"
    LIGHT = "light"
    READABLE = "readable"
    LLM = "llm"


class ExecutionStatus(str, Enum):
    """Status of diagram execution."""
    STARTED = "started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class DBBlockSubType(str, Enum):
    """Subtypes for database blocks."""
    FIXED_PROMPT = "fixed_prompt"
    FILE = "file"
    CODE = "code"


class ContentType(str, Enum):
    """Types of content in the system."""
    VARIABLE = "variable"
    RAW_TEXT = "raw_text"
    CONVERSATION_STATE = "conversation_state"


class ContextCleaningRule(str, Enum):
    """Rules for cleaning LLM context."""
    ON_EVERY_TURN = "on_every_turn"
    UPON_REQUEST = "upon_request"
    NO_FORGET = "no_forget"