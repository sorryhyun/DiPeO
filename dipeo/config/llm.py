"""LLM configuration constants for DiPeO."""

# Default LLM parameters
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 128000

# PersonJob specific parameters (more deterministic for job execution)
PERSON_JOB_TEMPERATURE = 0.1
PERSON_JOB_MAX_TOKENS = 128000

# Memory selection parameters (deterministic)
MEMORY_SELECTION_TEMPERATURE = 0.0
MEMORY_SELECTION_MAX_TOKENS = 500

# Model-specific defaults
ANTHROPIC_DEFAULT_MAX_TOKENS = 128000
OPENAI_DEFAULT_MAX_TOKENS = 128000
GEMINI_DEFAULT_MAX_TOKENS = 128000

# Temperature ranges
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0

# Token limits
MIN_MAX_TOKENS = 1
MAX_MAX_TOKENS = 128000  # Most models support up to 128k