"""LLM configuration constants for DiPeO."""

# Default LLM parameters
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 128000

# Execution phase-specific parameters
# PersonJob phase (more deterministic for job execution)
PERSON_JOB_TEMPERATURE = 0.1
PERSON_JOB_MAX_TOKENS = 128000

# Memory selection phase (deterministic)
MEMORY_SELECTION_TEMPERATURE = 0.0
MEMORY_SELECTION_MAX_TOKENS = 32000  # Memory selection responses are concise

# Decision evaluation phase (binary decisions)
DECISION_EVALUATION_TEMPERATURE = 0.0
DECISION_EVALUATION_MAX_TOKENS = 32000  # Decisions should be concise

# Temperature ranges
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0

# Token limits
MIN_MAX_TOKENS = 1
MAX_MAX_TOKENS = 128000  # System-wide maximum

# Provider-specific context and output limits
# Claude Code
CLAUDE_MAX_CONTEXT_LENGTH = 200000
CLAUDE_MAX_OUTPUT_TOKENS = 128000

# Anthropic (standard Claude)
ANTHROPIC_MAX_CONTEXT_LENGTH = 200000
ANTHROPIC_MAX_OUTPUT_TOKENS = 128000

# OpenAI
OPENAI_MAX_CONTEXT_LENGTH = 128000  # GPT-4o default
OPENAI_MAX_OUTPUT_TOKENS = 128000

# Google
GOOGLE_MAX_CONTEXT_LENGTH = 1048576  # Gemini 1.5 Pro context window
GOOGLE_MAX_OUTPUT_TOKENS = 128000

# Ollama (defaults - varies by model)
OLLAMA_DEFAULT_MAX_CONTEXT_LENGTH = 128000
OLLAMA_DEFAULT_MAX_OUTPUT_TOKENS = 4096
