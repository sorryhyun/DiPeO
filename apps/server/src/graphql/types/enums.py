"""Enum types for DiPeO GraphQL schema."""
import strawberry
from enum import Enum

@strawberry.enum
class NodeType(Enum):
    START = "start"
    PERSON_JOB = "person_job"
    CONDITION = "condition"
    JOB = "job"
    ENDPOINT = "endpoint"
    DB = "db"
    USER_RESPONSE = "user_response"
    NOTION = "notion"
    PERSON_BATCH_JOB = "person_batch_job"

@strawberry.enum
class HandleDirection(Enum):
    IN = "in"
    OUT = "out"

@strawberry.enum
class DataType(Enum):
    ANY = "any"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"

@strawberry.enum
class LLMService(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    BEDROCK = "bedrock"
    VERTEX = "vertex"
    DEEPSEEK = "deepseek"

@strawberry.enum
class ForgettingMode(Enum):
    NONE = "none"
    ON_EVERY_TURN = "on_every_turn"
    UPON_REQUEST = "upon_request"

@strawberry.enum
class ExecutionStatus(Enum):
    STARTED = "started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"

@strawberry.enum
class EventType(Enum):
    EXECUTION_STARTED = "execution_started"
    NODE_STARTED = "node_started"
    NODE_PROGRESS = "node_progress"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    NODE_SKIPPED = "node_skipped"
    NODE_PAUSED = "node_paused"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_ABORTED = "execution_aborted"
    INTERACTIVE_PROMPT = "interactive_prompt"
    INTERACTIVE_RESPONSE = "interactive_response"