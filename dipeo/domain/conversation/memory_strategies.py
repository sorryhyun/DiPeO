"""Memory selection strategies for conversation management.

This module provides a strategy pattern for memory selection,
simplifying the previous Brain-based architecture.
"""

import math
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from dipeo.config.memory import (
    MEMORY_CONTENT_KEY_LENGTH,
    MEMORY_DECAY_FACTOR,
    MEMORY_HARD_CAP,
    MEMORY_SCORING_WEIGHTS,
    MEMORY_WORD_OVERLAP_THRESHOLD,
)
from dipeo.diagram_generated.domain_models import Message, PersonID

if TYPE_CHECKING:
    from dipeo.domain.conversation.ports import MemorySelectionPort


@dataclass
class MemoryConfig:
    """Configuration for memory selection behavior."""

    hard_cap: int = MEMORY_HARD_CAP
    decay_factor: int = MEMORY_DECAY_FACTOR
    word_overlap_threshold: float = MEMORY_WORD_OVERLAP_THRESHOLD
    default_weights: dict[str, float] = field(default_factory=lambda: MEMORY_SCORING_WEIGHTS.copy())


class MemorySelectionStrategy(ABC):
    """Abstract base class for memory selection strategies."""

    @abstractmethod
    async def select_memories(
        self,
        candidate_messages: Sequence[Message],
        prompt_preview: str,
        memorize_to: str | None,
        ignore_person: str | None,
        at_most: int | None,
        **kwargs,
    ) -> list[Message] | None:
        """Select relevant memories based on criteria.

        Args:
            candidate_messages: Messages to select from
            prompt_preview: Preview of the upcoming task
            memorize_to: Selection criteria
            ignore_person: Comma-separated list of person IDs to exclude
            at_most: Maximum messages to select
            **kwargs: Additional parameters

        Returns:
            Selected messages or None if no selection performed
        """
        pass


class DefaultMemoryStrategy(MemorySelectionStrategy):
    """Default memory strategy that returns all messages for the person."""

    async def select_memories(
        self,
        candidate_messages: Sequence[Message],
        prompt_preview: str,
        memorize_to: str | None,
        ignore_person: str | None,
        at_most: int | None,
        **kwargs,
    ) -> list[Message] | None:
        if not memorize_to:
            return None

        if memorize_to.strip().upper() == "GOLDFISH":
            return []

        if at_most:
            return list(candidate_messages[:at_most])
        return list(candidate_messages)


class IntelligentMemoryStrategy(MemorySelectionStrategy):
    """Memory strategy using LLM-based intelligent selection with scoring and deduplication."""

    def __init__(
        self,
        memory_selector: Optional["MemorySelectionPort"] = None,
        config: MemoryConfig | None = None,
    ):
        self.config = config or MemoryConfig()
        self.memory_selector = memory_selector

    async def select_memories(
        self,
        candidate_messages: Sequence[Message],
        prompt_preview: str,
        memorize_to: str | None,
        ignore_person: str | None,
        at_most: int | None,
        **kwargs,
    ) -> list[Message] | None:
        if not memorize_to or not memorize_to.strip():
            return None

        if memorize_to.strip().upper() == "GOLDFISH":
            return []

        if not self.memory_selector:
            return None

        filtered_candidates = self._filter_messages(candidate_messages, ignore_person)

        unique_messages, frequencies = self._deduplicate_messages(filtered_candidates)

        scored_messages = self._score_and_rank_messages(
            unique_messages, frequencies, datetime.now()
        )

        top_candidates = [msg for msg, score in scored_messages[: self.config.hard_cap]]

        person_id = kwargs.pop("person_id", PersonID("system"))
        selected_ids = await self.memory_selector.select_memories(
            person_id=person_id,
            candidate_messages=top_candidates,
            task_preview=prompt_preview,
            criteria=memorize_to,
            at_most=at_most,
            preprocessed=True,
            **kwargs,
        )

        if selected_ids is None:
            return None

        idset = set(selected_ids)
        return [m for m in filtered_candidates if m.id and m.id in idset]

    def _filter_messages(
        self, messages: Sequence[Message], ignore_person: str | None
    ) -> list[Message]:
        ignored_persons = set()
        if ignore_person:
            ignored_persons = {p.strip() for p in ignore_person.split(",") if p.strip()}

        filtered = []
        for msg in messages:
            if msg.from_person_id and ".__selector" in str(msg.from_person_id):
                continue
            if msg.to_person_id and ".__selector" in str(msg.to_person_id):
                continue

            if ignored_persons and msg.from_person_id:
                if str(msg.from_person_id) in ignored_persons:
                    continue

            filtered.append(msg)

        return filtered

    def _deduplicate_messages(
        self, messages: Sequence[Message]
    ) -> tuple[list[Message], dict[str, int]]:
        unique_messages = []
        frequencies = {}
        seen_contents = []

        for message in messages:
            if not getattr(message, "id", None):
                continue

            content_key = (message.content or "")[:MEMORY_CONTENT_KEY_LENGTH].strip()

            is_duplicate = False
            for seen_content, seen_msg in seen_contents:
                if self._calculate_word_overlap(content_key, seen_content):
                    frequencies[seen_msg.id] = frequencies.get(seen_msg.id, 1) + 1
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_messages.append(message)
                frequencies[message.id] = 1
                seen_contents.append((content_key, message))

        return unique_messages, frequencies

    def _calculate_word_overlap(self, text1: str, text2: str) -> bool:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return text1 == text2

        intersection = len(words1 & words2)
        smaller_set = min(len(words1), len(words2))

        return (intersection / smaller_set) >= self.config.word_overlap_threshold

    def _score_and_rank_messages(
        self,
        messages: Sequence[Message],
        frequencies: dict[str, int],
        current_time: datetime,
    ) -> list[tuple[Message, float]]:
        scored_messages = []

        for msg in messages:
            if not getattr(msg, "id", None):
                continue

            score = self._score_message(msg, frequencies.get(msg.id, 1), current_time)
            scored_messages.append((msg, score))

        scored_messages.sort(key=lambda x: x[1], reverse=True)
        return scored_messages

    def _score_message(
        self,
        message: Message,
        frequency_count: int,
        current_time: datetime,
    ) -> float:
        weights = self.config.default_weights
        scores = {}

        if message.timestamp and current_time:
            try:
                msg_time = datetime.fromisoformat(message.timestamp.replace("Z", "+00:00"))
                age_seconds = (current_time - msg_time).total_seconds()
                scores["recency"] = 100 * math.exp(-age_seconds / self.config.decay_factor)
            except (ValueError, AttributeError):
                scores["recency"] = 50
        else:
            scores["recency"] = 50

        scores["frequency"] = min(100, 30 + (frequency_count - 1) * 20)

        if message.from_person_id == PersonID("system"):
            scores["frequency"] = min(100, scores["frequency"] + 30)

        total_score = sum(scores.get(factor, 0) * weight for factor, weight in weights.items())

        return total_score


class SimpleMemoryStrategy(MemorySelectionStrategy):
    """Simple memory strategy with basic filtering rules."""

    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages

    async def select_memories(
        self,
        candidate_messages: Sequence[Message],
        prompt_preview: str,
        memorize_to: str | None,
        ignore_person: str | None,
        at_most: int | None,
        **kwargs,
    ) -> list[Message] | None:
        if not memorize_to:
            return None

        if memorize_to.strip().upper() == "GOLDFISH":
            return []

        limit = at_most or self.max_messages
        return list(candidate_messages[-limit:])
