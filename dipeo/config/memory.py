"""Memory selection and processing configuration for DiPeO.

Configuration Guide:
- MEMORY_HARD_CAP: Maximum candidates to pass to LLM for selection
  - Default 150 should be sufficient for most cases
  - Increase if you need more candidates (e.g., 200-300 for very large conversations)
  - Decrease for faster processing with smaller token budgets (e.g., 50-100)

- MEMORY_WORD_OVERLAP_THRESHOLD: Similarity threshold for deduplication (0.0-1.0)
  - Default 0.8 means 80% word overlap triggers deduplication
  - Lower values (0.6-0.7) = more aggressive deduplication = fewer candidates
  - Higher values (0.9-0.95) = less aggressive = more candidates may remain
  - Set to 1.0 to only deduplicate exact duplicates

- MEMORY_DECAY_FACTOR: How quickly message importance decays over time
  - Default 3600 seconds (1 hour)
  - Lower values = older messages decay faster
  - Higher values = older messages remain relevant longer
"""

# Memory selection hard limits
MEMORY_HARD_CAP = 150  # Maximum messages to show in memory selection listing
MEMORY_DECAY_FACTOR = 3600  # 1 hour in seconds for recency decay calculation

# Content processing limits
MEMORY_TASK_PREVIEW_MAX_LENGTH = 1200  # Maximum characters for task preview in selection prompt
MEMORY_CRITERIA_MAX_LENGTH = 750  # Maximum characters for selection criteria
MEMORY_CONTENT_SNIPPET_LENGTH = 250  # Maximum characters for message snippet in listing
MEMORY_CONTENT_KEY_LENGTH = 400  # Maximum characters for content key in deduplication

# Deduplication settings
MEMORY_WORD_OVERLAP_THRESHOLD = 0.9  # 80% word overlap threshold for deduplication

# Scoring weights for message ranking
MEMORY_SCORING_WEIGHTS = {
    "recency": 0.7,  # Weight for message recency (70%)
    "frequency": 0.3,  # Weight for message frequency (30%)
    "relevance": 0.0,  # Reserved for future semantic relevance scoring
    "position": 0.0,  # Reserved for future position-based scoring
}
