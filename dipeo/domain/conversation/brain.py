"""Domain logic for cognitive brain with memory selection and scoring."""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, TypedDict

from dipeo.diagram_generated.domain_models import Message, PersonID

if TYPE_CHECKING:
    from dipeo.application.execution.handlers.person_job.memory_selector import MemorySelector
    from dipeo.application.execution.orchestrators.execution_orchestrator import (
        ExecutionOrchestrator,
    )


class ScoringWeights(TypedDict):
    """Weights for different scoring factors."""
    recency: float
    frequency: float
    relevance: float
    position: float


@dataclass
class MemorySelectionConfig:
    """Configuration for memory selection behavior."""
    hard_cap: int = 30  # Maximum messages to show in listing
    decay_factor: int = 3600  # 1 hour in seconds for recency decay
    default_weights: ScoringWeights = field(default_factory=lambda: {
        'recency': 0.6,  # 60% weight on recency
        'frequency': 0.4,  # 40% weight on frequency
        'relevance': 0.0,  # Not used currently
        'position': 0.0   # Not used currently
    })
    word_overlap_threshold: float = 0.8  # 80% word overlap for deduplication


class MessageScorer:
    """Handles scoring of messages based on various factors."""
    
    def __init__(self, config: MemorySelectionConfig):
        self.config = config
    
    def score_message(
        self,
        message: Message,
        frequency_count: int = 1,
        current_time: datetime | None = None,
        weights: ScoringWeights | None = None
    ) -> float:
        """Calculate a composite score for a message based on multiple factors.
        
        Args:
            message: The message to score
            frequency_count: How many similar messages exist
            current_time: Current time for recency calculation
            weights: Custom weights for scoring factors
            
        Returns:
            Float score between 0-100
        """
        if weights is None:
            weights = self.config.default_weights
        
        scores = {}
        
        # 1. Recency Score (0-100)
        if message.timestamp and current_time:
            try:
                msg_time = datetime.fromisoformat(message.timestamp.replace('Z', '+00:00'))
                age_seconds = (current_time - msg_time).total_seconds()
                scores['recency'] = 100 * math.exp(-age_seconds / self.config.decay_factor)
            except (ValueError, AttributeError):
                scores['recency'] = 50  # Default middle score if timestamp parsing fails
        else:
            scores['recency'] = 50
        
        # 2. Frequency/Importance Score (0-100)
        scores['frequency'] = min(100, 30 + (frequency_count - 1) * 20)
        
        # Boost system messages
        if message.from_person_id == PersonID("system"):
            scores['frequency'] = min(100, scores['frequency'] + 30)
        
        # Calculate weighted composite score
        total_score = sum(
            scores.get(factor, 0) * weight 
            for factor, weight in weights.items()
        )
        
        return total_score
    
    def score_messages(
        self,
        messages: Sequence[Message],
        frequencies: dict[str, int] | None = None,
        current_time: datetime | None = None,
        weights: ScoringWeights | None = None
    ) -> dict[str, float]:
        """Score multiple messages and return a dict of message ID to score.
        
        Args:
            messages: Messages to score
            frequencies: Optional frequency counts per message ID
            current_time: Current time for recency calculation
            weights: Custom weights for scoring factors
            
        Returns:
            Dict mapping message ID to score
        """
        scores = {}
        freq_map = frequencies or {}
        
        for msg in messages:
            if not getattr(msg, "id", None):
                continue
            freq = freq_map.get(msg.id, 1)
            scores[msg.id] = self.score_message(
                msg, freq, current_time, weights
            )
        
        return scores


class MessageDeduplicator:
    """Handles deduplication of similar messages."""
    
    def __init__(self, config: MemorySelectionConfig):
        self.config = config
    
    def calculate_word_overlap(self, text1: str, text2: str) -> bool:
        """Check if two texts have sufficient word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return text1 == text2
        
        intersection = len(words1 & words2)
        smaller_set = min(len(words1), len(words2))
        
        return (intersection / smaller_set) >= self.config.word_overlap_threshold
    
    def deduplicate(
        self, 
        messages: Sequence[Message],
        return_frequencies: bool = False
    ) -> tuple[list[Message], dict[str, int]] | list[Message]:
        """Deduplicate similar messages.
        
        Args:
            messages: Messages to deduplicate
            return_frequencies: Whether to return frequency counts
            
        Returns:
            If return_frequencies=True: (unique_messages, frequencies)
            Otherwise: unique_messages
        """
        unique_messages = []
        frequencies = {}  # Maps message ID to frequency count
        seen_contents = []  # Track (content_key, message)
        
        for message in messages:
            if not getattr(message, "id", None):
                continue
            
            # Get content for deduplication check
            content_key = (message.content or "")[:400].strip()
            
            # Check if this message is a duplicate of an existing one
            is_duplicate = False
            for seen_content, seen_msg in seen_contents:
                if self.calculate_word_overlap(content_key, seen_content):
                    # This is a duplicate - increment frequency
                    frequencies[seen_msg.id] = frequencies.get(seen_msg.id, 1) + 1
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                # This is a unique message
                unique_messages.append(message)
                frequencies[message.id] = 1
                seen_contents.append((content_key, message))
        
        if return_frequencies:
            return unique_messages, frequencies
        return unique_messages


def apply_message_limit(
    messages: Sequence[Message],
    limit: int | None
) -> list[Message]:
    """Apply message count limit while always preserving system messages.
    
    Args:
        messages: Messages to limit
        limit: Maximum number of messages (None means no limit)
        
    Returns:
        Limited list of messages with system messages always preserved
    """
    if not limit or limit <= 0 or len(messages) <= limit:
        return list(messages)
    
    # Always preserve system messages
    system_messages = [
        msg for msg in messages 
        if msg.from_person_id == PersonID("system")
    ]
    non_system_messages = [
        msg for msg in messages 
        if msg.from_person_id != PersonID("system")
    ]
    
    # Calculate available slots for non-system messages
    available_slots = limit - len(system_messages)
    if available_slots <= 0:
        # If system messages exceed limit, take the most recent ones
        return system_messages[-limit:]
    
    # Take most recent non-system messages within available slots
    return system_messages + non_system_messages[-available_slots:]


class CognitiveBrain:
    """Cognitive utilities: selection, analysis, planning.
    
    Integrates memory selection, scoring, and filtering capabilities
    directly for a cleaner API.
    """
    
    def __init__(self, orchestrator: "ExecutionOrchestrator", config: MemorySelectionConfig | None = None):
        """Initialize with orchestrator for proper integration.
        
        Args:
            orchestrator: The execution orchestrator for accessing shared components
            config: Optional memory selection configuration
        """
        self._orchestrator = orchestrator
        
        # Initialize domain memory components directly
        self._config = config or MemorySelectionConfig()
        self._scorer = MessageScorer(self._config)
        self._deduplicator = MessageDeduplicator(self._config)
        
        # Lazy initialization of LLM-based selector to avoid circular dependencies
        self._selector: MemorySelector | None = None
    
    def _get_selector(self) -> "MemorySelector":
        """Get or create the memory selector instance for LLM-based selection."""
        if self._selector is None:
            from dipeo.application.execution.handlers.person_job.memory_selector import (
                MemorySelector,
            )
            self._selector = MemorySelector(self._orchestrator, self._config)
        return self._selector

    async def select_memories(
        self,
        *,
        person,  # Add person parameter for proper context
        candidate_messages: Sequence[Message],
        prompt_preview: str,
        memorize_to: str | None,
        at_most: int | None,
        llm_service=None,  # Add llm_service for selector
    ) -> list[Message] | None:
        """Select relevant memories based on criteria.
        
        Args:
            person: The person for memory selection context
            candidate_messages: Messages to select from
            prompt_preview: Preview of the upcoming task
            memorize_to: Selection criteria (GOLDFISH for empty, string for LLM selection)
            at_most: Maximum messages to select
            llm_service: LLM service for intelligent selection
            
        Returns:
            Selected messages or None if no criteria specified
        """
        if not (isinstance(memorize_to, str) and memorize_to.strip()):
            return None
        if memorize_to.strip().upper() == "GOLDFISH":
            return []  # Empty context for goldfish mode
        
        # Use the memory selector for intelligent selection
        selector = self._get_selector()
        selected_ids = await selector.select(
            person=person,
            candidate_messages=candidate_messages,
            task_prompt_preview=prompt_preview,
            criteria=memorize_to,
            at_most=at_most,
            llm_service=llm_service,
        )
        if not selected_ids:
            return None
        
        # Map IDs back to messages and preserve system messages
        idset = set(selected_ids)
        system = [m for m in candidate_messages if str(m.from_person_id) == "system"]
        selected = [m for m in candidate_messages if m.id and m.id in idset]
        
        # Apply limit while preserving system messages
        combined = system + selected
        return apply_message_limit(combined, at_most)

    
    def score_message(
        self, 
        message: Message,
        frequency_count: int = 1,
        current_time: datetime | None = None
    ) -> float:
        """Score a message based on recency and frequency.
        
        Args:
            message: The message to score
            frequency_count: How many similar messages exist
            current_time: Current time for recency calculation
            
        Returns:
            Float score between 0-100
        """
        return self._scorer.score_message(
            message, 
            frequency_count=frequency_count,
            current_time=current_time or datetime.now()
        )
    
    def deduplicate_messages(
        self,
        messages: Sequence[Message],
        return_frequencies: bool = False
    ) -> tuple[list[Message], dict[str, int]] | list[Message]:
        """Deduplicate similar messages.
        
        Args:
            messages: Messages to deduplicate
            return_frequencies: Whether to return frequency counts
            
        Returns:
            If return_frequencies=True: (unique_messages, frequencies)
            Otherwise: unique_messages
        """
        return self._deduplicator.deduplicate(messages, return_frequencies)
    
    def score_and_rank_messages(
        self,
        messages: Sequence[Message],
        frequencies: dict[str, int] | None = None,
        current_time: datetime | None = None
    ) -> list[tuple[Message, float]]:
        """Score messages and return them ranked by score.
        
        Args:
            messages: Messages to score
            frequencies: Optional frequency counts per message ID
            current_time: Current time for recency calculation
            
        Returns:
            List of (message, score) tuples sorted by score (descending)
        """
        scores = self._scorer.score_messages(
            messages,
            frequencies=frequencies,
            current_time=current_time or datetime.now()
        )
        
        # Create list of (message, score) and sort by score
        scored_messages = [
            (msg, scores.get(msg.id, 0.0))
            for msg in messages
            if getattr(msg, "id", None)
        ]
        scored_messages.sort(key=lambda x: x[1], reverse=True)
        return scored_messages
    
    def apply_message_limit(
        self,
        messages: Sequence[Message],
        at_most: int | None
    ) -> list[Message]:
        """Apply message count limit while preserving system messages.
        
        Args:
            messages: Messages to limit
            at_most: Maximum number of messages
            
        Returns:
            Limited list of messages with system messages preserved
        """
        return apply_message_limit(messages, at_most)