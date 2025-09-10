"""Memory selection and processing configuration for DiPeO."""

# Memory selection hard limits
MEMORY_HARD_CAP = 150  # Maximum messages to show in memory selection listing
MEMORY_DECAY_FACTOR = 3600  # 1 hour in seconds for recency decay calculation

# Content processing limits
MEMORY_TASK_PREVIEW_MAX_LENGTH = 1200  # Maximum characters for task preview in selection prompt
MEMORY_CRITERIA_MAX_LENGTH = 750  # Maximum characters for selection criteria
MEMORY_CONTENT_SNIPPET_LENGTH = 250  # Maximum characters for message snippet in listing
MEMORY_CONTENT_KEY_LENGTH = 400  # Maximum characters for content key in deduplication

# Deduplication settings
MEMORY_WORD_OVERLAP_THRESHOLD = 0.8  # 80% word overlap threshold for deduplication

# Scoring weights for message ranking
MEMORY_SCORING_WEIGHTS = {
    "recency": 0.7,  # Weight for message recency (70%)
    "frequency": 0.3,  # Weight for message frequency (30%)
    "relevance": 0.0,  # Reserved for future semantic relevance scoring
    "position": 0.0,  # Reserved for future position-based scoring
}
