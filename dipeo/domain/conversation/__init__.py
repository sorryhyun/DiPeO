"""Dynamic objects that maintain state during diagram execution."""

from .conversation import Conversation, ConversationContext
from .person import Person
from .brain import (
    CognitiveBrain,
    MemorySelectionConfig,
    MessageScorer,
    MessageDeduplicator,
    ScoringWeights,
)

__all__ = [
    # Dynamic objects
    "Conversation",
    "ConversationContext", 
    "Person",
    # Cognitive components
    "CognitiveBrain",
    # Memory selection
    "MemorySelectionConfig",
    "MessageScorer",
    "MessageDeduplicator",
    "ScoringWeights",
]